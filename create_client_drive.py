from classifier import classify_crm_fields
from read_mails import retrieve_message_list
from services import get_drive_service

from dotenv import load_dotenv

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

# get api key from .env
load_dotenv()
DRIVE_ID = os.getenv("GOOGLE_DRIVE_ID")  # dossier racine clients

# initialize system prompt
system_prompt = open("system_prompt_classifier.txt", "r", encoding="utf-8").read()

def create_client_drive(drive_service, prenom, nom, email, parent_id):
    """
    Crée (ou récupère) un dossier Drive pour un contact.
    Nom du dossier :
        - 'Nom Prénom - email' si nom/prénom/email dispo
        - 'Nom Prénom' si pas d'email
        - 'email' si pas de nom/prénom
    Si le dossier existe déjà dans parent_id, renvoie son id.
    Sinon, le crée et renvoie son id.
    """
    prenom = (prenom or "").strip()
    nom = (nom or "").strip()
    email = (email or "").strip()

    if not prenom and not nom and not email:
        return None  # aucune info -> on ne crée rien

    if nom and prenom and email:
        folder_name = f"{nom} {prenom} - {email}"
    elif nom or prenom:
        folder_name = f"{nom} {prenom}".strip()
    else:
        folder_name = email  # pas de nom/prénom mais email dispo

    # Recherche d'un dossier existant
    query = (
        "mimeType = 'application/vnd.google-apps.folder' "
        f"and name = '{folder_name}' "
        f"and '{parent_id}' in parents "
        "and trashed = false"
    )

    try:
        resp = drive_service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
            pageSize=1,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

        files = resp.get("files", [])
        if files:
            # Dossier déjà existant
            return files[0]["id"]

        # Sinon on le crée
        metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }

        folder = drive_service.files().create(
            body=metadata,
            fields="id",
            supportsAllDrives=True,
        ).execute()

        return folder.get("id")

    except HttpError as e:
        print(f"[Drive] Erreur pour le dossier '{folder_name}': {e}")
        return None



def attach_drive_folders_to_messages(drive_service, classified_messages, drive_id):
    """
    Pour chaque message classifié, crée/récupère un dossier client
    et ajoute 'drive_folder_id' dans le dict.
    """
    for msg in classified_messages:
        prenom = msg.get("Prénom") or msg.get("prenom")
        nom = msg.get("Nom") or msg.get("nom")
        email = msg.get("Email") or msg.get("email")

        folder_id = create_client_drive(drive_service, prenom, nom, email, drive_id)
        msg["drive_folder_id"] = folder_id

    return classified_messages



built_message_list = retrieve_message_list()
classified_messages = classify_crm_fields(built_message_list, system_prompt)

drive_service = get_drive_service()

attach_drive_folders_to_messages(drive_service, classified_messages, DRIVE_ID)
#print("Total classified messages :", len(classified_messages)) 
