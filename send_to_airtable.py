import os
import requests

from dotenv import load_dotenv

load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

"""
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
"""

import requests

def check_matching_record(record, airtable_table_id, airtable_base_id, airtable_api_key):
    """
    Cherche un enregistrement existant dans Airtable qui correspond au record donné.
    Logique de 'doublon' centralisée ici.
    Renvoie le premier enregistrement trouvé (dict Airtable complet) ou None.
    """
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
        # fallback sur Nom + Prénom + Ville
        formula = f"AND({{Nom}} = '{nom}', {{Prénom}} = '{prenom}', {{Ville}} = '{ville}')"

    response = requests.get(url, headers=headers, params={"filterByFormula": formula})
    data = response.json()

    records = data.get("records", [])
    if not records:
        return None

    # On retourne le premier match
    return records[0]


def check_null_value(field_name, value):
    """
    Renvoie False si le champ doit être ignoré (considéré comme 'vide'),
    True sinon.

    Version simple : on ignore None, chaîne vide, liste vide.
    """
    if value in (None, "", []):
        return False
    return True

def build_airtable_fields_from_record(record):
    """
    Construit le dict 'fields' pour Airtable à partir de ton record Python.
    Convertit les listes Jours/Plages en chaînes.
    Construit aussi le lien Google Drive à partir de drive_folder_id si besoin.
    Applique check_null_value pour décider quels champs on garde.
    """
    jours = record.get("Jours disponibles") or []
    plages = record.get("Plages horaires") or []

    if isinstance(jours, list):
        jours_str = "/".join(jours)
    else:
        jours_str = str(jours)

    if isinstance(plages, list):
        plages_str = "/".join(plages)
    else:
        plages_str = str(plages)

    # 🔗 Construire le lien Drive
    drive_link = record.get("Lien dossier Google Drive")
    if not drive_link:
        folder_id = record.get("drive_folder_id")
        if folder_id:
            drive_link = f"https://drive.google.com/drive/folders/{folder_id}"

    raw_fields = {
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

        "Jours disponibles": jours_str,
        "Plages horaires": plages_str,
        "Statut du dossier": record.get("Statut du dossier"),
        "Lien dossier Google Drive": drive_link,
    }

    # On applique check_null_value champ par champ
    fields = {
        k: v for k, v in raw_fields.items()
        if check_null_value(k, v)
    }

    return fields


def add_record_to_airtable(data, airtable_table_id, airtable_base_id, airtable_api_key):
    url = f"https://api.airtable.com/v0/{airtable_base_id}/{airtable_table_id}"

    headers = {
        "Authorization": f"Bearer {airtable_api_key}",
        "Content-Type": "application/json",
    }

    for record in data:
        # 1) Chercher un éventuel enregistrement existant correspondant
        existing = check_matching_record(
            record,
            airtable_table_id,
            airtable_base_id,
            airtable_api_key
        )

        fields = build_airtable_fields_from_record(record)

        if existing:
            existing_id = existing["id"]
            existing_fields = existing.get("fields", {})

            # 2) Déterminer quels champs ont réellement changé
            fields_to_update = {}
            for key, new_value in fields.items():
                old_value = existing_fields.get(key)
                if str(old_value) != str(new_value):  # comparaison simple
                    fields_to_update[key] = new_value

            if not fields_to_update:
                print(f"[SKIP] Aucun changement pour {record.get('Email') or record.get('Nom')}")
                continue

            # 3) Mise à jour du record existant (PATCH)
            update_url = f"{url}/{existing_id}"
            resp = requests.patch(update_url, headers=headers, json={"fields": fields_to_update})

            if resp.status_code == 200:
                print(f"[UPDATE] Record mis à jour pour {record.get('Email') or record.get('Nom')}")
            else:
                print(f"[FAILED UPDATE] {resp.status_code} {resp.text}")

        else:
            # 4) Aucun existant → création d'un nouvel enregistrement
            airtable_payload = {
                "records": [
                    {
                        "fields": fields
                    }
                ]
            }

            resp = requests.post(url, headers=headers, json=airtable_payload)
            if resp.status_code == 200:
                print("[CREATE] Record added successfully:", resp.json())
            else:
                print("[FAILED CREATE] Failed to add record:", resp.status_code, resp.text)
