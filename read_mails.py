import os
import base64
from datetime import datetime
from email.utils import parsedate_to_datetime

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

# SCOPES communs Gmail + Drive (read/write Gmail + créer fichiers/dossiers Drive)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive.file",
]


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
        
    plain_text = "\n".join(texts).strip()

    return plain_text


# ---------- 1) Gestion des credentials ----------

def get_creds():
    """
    Récupère des credentials valides en utilisant token.json / credentials.json
    avec les SCOPES définis plus haut.
    """
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Sauvegarde pour les prochains runs
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


# ---------- 2) Services Gmail / Drive ----------

def get_gmail_service():
    """
    Retourne un service Gmail prêt à l'emploi.
    """
    creds = get_creds()

    gmail_service = build("gmail", "v1", credentials=creds)

    return gmail_service


def get_drive_service():
    """
    Retourne un service Drive prêt à l'emploi (avec les mêmes creds).
    """
    creds = get_creds()

    drive_service = build("drive", "v3", credentials=creds)

    return drive_service


# ---------- 3) Construction de la liste de messages ----------

def build_messages_list(gmail_service):
    messages_list = []
    next_page_token = None

    while True:
        result = gmail_service.users().messages().list(
            userId="me",
            # q="is:unread",
            pageToken=next_page_token
        ).execute()

        messages = result.get("messages", [])

        for msg in messages:
            msg_id = msg["id"]
            msg_detail = gmail_service.users().messages().get(
                userId="me",
                id=msg_id,
                format="full"
            ).execute()

            payload = msg_detail.get("payload", {})
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

            synthese = msg_detail.get("snippet", "") or ""
            texte_complet = extract_plain_text(payload)
            if not texte_complet:
                texte_complet = synthese

            date_norm = None
            if date_header:
                try:
                    dt = parsedate_to_datetime(date_header)
                    date_norm = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    date_norm = date_header

            messages_list.append({
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

    return messages_list


def retrieve_message_list():
    """
    Fonction utilitaire "ancienne interface" :
    construit elle-même le service Gmail,
    puis retourne la liste de messages.
    """
    try:
        gmail_service = get_gmail_service()
        # Optionnel : juste pour vérifier que l'API répond
        _ = gmail_service.users().labels().list(userId="me").execute()
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

    return build_messages_list(gmail_service)
