import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def build_unread_messages_dict(service):

    unread_messages = []

    next_page_token = None

    while True:
        # Retrieve messages
        result = service.users().messages().list(
            userId="me",
            #q="is:unread",
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

            # Object 
            headers = msg_detail.get("payload", {}).get("headers", [])
            subject = ""
            for h in headers:
                if h.get("name") == "Subject":
                    subject = h.get("value", "")
                    break

            # Synthesis
            synthese = msg_detail.get("snippet", "")

            unread_messages.append({
                "id": msg_id,
                "sujet": subject,
                "urgence": "",
                "synthese": synthese,
            })

        next_page_token = result.get("nextPageToken")
        if not next_page_token:
            break
    return unread_messages


def main():

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

    unread_messages = build_unread_messages_dict(service)
    #print('Unread Message 192 : ', unread_messages[192])
    print('Unread Messages = ',len(unread_messages))

if __name__ == "__main__":
    main()