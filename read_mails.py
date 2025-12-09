import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

from email.utils import parsedate_to_datetime
from datetime import datetime

import base64
from email.utils import parsedate_to_datetime

def extract_plain_text(payload):
    """
    Récupère le texte brut d'un message Gmail (multipart ou non).
    On privilégie text/plain, sinon on prend text/html tel quel.
    """
    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})
    data = body.get("data")

    # Cas simple : une seule partie text/plain ou text/html
    if data and mime_type in ("text/plain", "text/html"):
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    # Cas multipart : on parcourt les sous-parties
    parts = payload.get("parts", [])
    texts = []

    for part in parts:
        part_mime = part.get("mimeType", "")
        part_body = part.get("body", {})
        part_data = part_body.get("data")

        if part_mime == "text/plain" and part_data:
            try:
                text = base64.urlsafe_b64decode(part_data).decode("utf-8", errors="ignore")
                texts.append(text)
            except Exception:
                continue
        elif part_mime.startswith("multipart/"):
            # récursif
            sub_text = extract_plain_text(part)
            if sub_text:
                texts.append(sub_text)
        elif not texts and part_mime == "text/html" and part_data:
            # fallback : si jamais on n'a pas de text/plain, on prend le HTML brut
            try:
                html = base64.urlsafe_b64decode(part_data).decode("utf-8", errors="ignore")
                texts.append(html)
            except Exception:
                continue

    return "\n".join(texts).strip()


def build_unread_messages_list(service):

    unread_messages = []
    next_page_token = None

    while True:
        # Retrieve messages
        result = service.users().messages().list(
            userId="me",
            # q="is:unread",
            pageToken=next_page_token
        ).execute()

        messages = result.get("messages", [])

        for msg in messages:
            msg_id = msg["id"]
            msg_detail = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="full"
            ).execute()

            payload = msg_detail.get("payload", {})  # pour le corps complet
            headers = payload.get("headers", [])

            subject = ""
            from_header = ""
            date_header = ""

            for h in headers:
                name = h.get("name", "")
                value = h.get("value", "")
                if name == "Subject":
                    subject = value
                elif name == "From":
                    from_header = value
                elif name == "Date":
                    date_header = value

            # Snippet = petite synthèse fournie par Gmail
            synthese = msg_detail.get("snippet", "") or ""

            # Corps complet
            texte_complet = extract_plain_text(payload)
            if not texte_complet:
                texte_complet = synthese  # fallback minimal

            # Normaliser la date au format "YYYY-MM-DD HH:MM:SS"
            date_norm = None
            if date_header:
                try:
                    dt = parsedate_to_datetime(date_header)
                    date_norm = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    date_norm = date_header  # au pire on garde brut

            unread_messages.append({
                "id": msg_id,
                "sujet": subject or "",
                "from": from_header or "",
                "date": date_norm,
                "urgence": "",
                "synthese": synthese,
                "texte_complet": texte_complet,
            })

        next_page_token = result.get("nextPageToken")
        if not next_page_token:
            break

    return unread_messages


def retrieve_message_list():

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        if not labels:
            print("No labels found.")
            return
        """
        print("Labels:")
        for label in labels:
            print(label["name"])
        """

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

    unread_messages = build_unread_messages_list(service)
    #print('Unread Message 192 : ', unread_messages[192])
    #print('Unread Messages = ',len(unread_messages))

    return unread_messages
