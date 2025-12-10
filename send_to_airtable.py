import os
import requests

from dotenv import load_dotenv

load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")


def check_duplicates(record, airtable_table_id, airtable_base_id, airtable_api_key):
    url = f"https://api.airtable.com/v0/{airtable_base_id}/{airtable_table_id}"
    headers = {"Authorization": f"Bearer {airtable_api_key}"}

    email = record.get("Email")
    tel = record.get("Téléphone")
    nom = record.get("Nom")
    prenom = record.get("Prénom")
    ville = record.get("Ville")

    if email:
        formula = f"{{Email}} = '{email}'"
    elif tel:
        formula = f"{{Téléphone}} = '{tel}'"
    else:
        formula = f"AND({{Nom}} = '{nom}', {{Prénom}} = '{prenom}', {{Ville}} = '{ville}')"

    response = requests.get(url, headers=headers, params={"filterByFormula": formula})
    data = response.json()

    return len(data.get("records", [])) > 0




def add_record_to_airtable(data, airtable_table_id, airtable_base_id,airtable_api_key):
    url= f"https://api.airtable.com/v0/{airtable_base_id}/{airtable_table_id}"

    auth_token =  airtable_api_key# API KEY --> .env
    headers = {
        "Authorization": f"Bearer {auth_token}",
        'id': airtable_base_id
    }   

    for record in data:
        # Check for duplicates
        if check_duplicates(record, airtable_table_id, airtable_base_id, airtable_api_key):
            print("Duplicate record found. Skipping:", record)
            continue
        airtable_payload = {
            "records": [
                {
                    "fields": {
                        "Prénom": record.get("Prénom"),
                        "Nom": record.get("Nom"),
                        "Email": record.get("Email"),
                        "Téléphone": record.get("Téléphone"),
                        "Adresse": record.get("Adresse"),
                        "Ville": record.get("Ville"),
                        "Code postal": record.get("Code postal"),
                        "Département": record.get("Département"),

                        "Titre du bien": record.get("Titre du bien"),
                        "Référence annonce": record.get("Référence"), 
                        "Ville du bien": record.get("Ville du bien"),
                        "Prix du bien": record.get("Prix du bien"),
                        "Référent": record.get("Référent"),

                        "Est propriétaire": record.get("Est propriétaire"),
                        "Objectif": record.get("Achète pour"),
                        "Type de bien recherché": record.get("Bien recherché"),
                        "Budget d’achat": record.get("Budget d achat"),
                        "Dossier de financement": record.get("A un dossier de financement"),
                        "Délai d’achat": record.get("Délai d achat"),
                        "Secteurs de recherche": record.get("Secteurs de recherche"),
                        "Intérêt programme neuf": record.get("Est intéressé par du programme neuf"),

                        "Jours disponibles": "/".join(record.get("Jours disponibles")),
                        "Plages horaires": "/".join(record.get("Plages horaires")),
                        "Statut du dossier": record.get("Statut du dossier"),
                        "Lien dossier Google Drive": None
                        #"Formulaire": False,
                    }
                }
            ]
        }

        response = requests.post(url, headers=headers, json=airtable_payload)
        if response.status_code == 200:
            print("Record added successfully:", response.json())
        else:
            print("Failed to add record:", response.status_code, response.text)