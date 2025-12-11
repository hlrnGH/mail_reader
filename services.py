# services.py

import os
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# SCOPES COMMUNS (Gmail + Drive + Calendar)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",   # lire/archiver/étiqueter
    "https://www.googleapis.com/auth/gmail.send",     # envoyer des mails
    "https://www.googleapis.com/auth/drive.file",     # créer/écrire sur Drive
    "https://www.googleapis.com/auth/calendar"        # gérer le calendrier
]

TOKEN_PATH = "token.json"
CREDENTIALS_PATH = "credentials.json"


# 1) Gestion des credentials

def get_creds():
    """
    Récupère des credentials OAuth2 valides en utilisant token.json / credentials.json
    pour les SCOPES définis plus haut.
    """
    creds = None

    # On tente de charger un token existant
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # Si pas de creds ou invalide → refresh ou nouveau flow OAuth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh silencieux
            creds.refresh(Request())
        else:
            # Nouveau flow OAuth dans le navigateur
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Sauvegarde pour les prochains runs
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return creds


# 2) Services Google

def get_gmail_service():
    """
    Retourne un service Gmail prêt à l'emploi.
    """
    creds = get_creds()
    return build("gmail", "v1", credentials=creds)


def get_drive_service():
    """
    Retourne un service Drive prêt à l'emploi.
    """
    creds = get_creds()
    return build("drive", "v3", credentials=creds)


def get_calendar_service():
    """
    Retourne un service Google Calendar prêt à l'emploi.
    """
    creds = get_creds()
    return build("calendar", "v3", credentials=creds)
