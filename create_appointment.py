# create_appointment.py

import re
import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

import requests

from services import get_calendar_service  # <- on réutilise ton fichier services.py

# ---------------- CONFIG ----------------

TIMEZONE = "Europe/Paris"
tz = ZoneInfo(TIMEZONE)

DEFAULT_MEETING_DURATION_MIN = 60   # durée d’un RDV en minutes
DEFAULT_LOOKAHEAD_DAYS = 7          # fenêtre de recherche pour les conflits dans le calendrier
# ----------------------------------------


def fetch_airtable_records(airtable_api_key, airtable_base_id, airtable_table_id):
    """
    Récupère tous les enregistrements d'une table Airtable.
    Renvoie une liste de dicts = les 'fields' de chaque record.
    """
    url = f"https://api.airtable.com/v0/{airtable_base_id}/{airtable_table_id}"
    headers = {"Authorization": f"Bearer {airtable_api_key}"}

    records = []
    offset = None

    while True:
        params = {}
        if offset:
            params["offset"] = offset

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        for r in data.get("records", []):
            fields = r.get("fields", {})
            records.append(fields)

        offset = data.get("offset")
        if not offset:
            break

    return records


def parse_plage(plage_str):
    """
    Transforme une plage horaire texte ('Entre 9h et 12h', '18h-20h', '9:30-11:00')
    en deux couples (h_debut, m_debut), (h_fin, m_fin).
    """
    if not isinstance(plage_str, str):
        raise ValueError("Plage invalide")

    # Uniformiser 'h' en ':'
    plage_norm = plage_str.replace("h", ":")

    # On cherche des patterns 'HH' ou 'HH:MM'
    heures = re.findall(r"\d{1,2}(?::\d{1,2})?", plage_norm)
    if len(heures) >= 2:
        def to_time(s):
            if ":" in s:
                h, m = s.split(":")
                return int(h), int(m)
            else:
                return int(s), 0

        sh, sm = to_time(heures[0])
        eh, em = to_time(heures[1])
        return (sh, sm), (eh, em)

    raise ValueError(f"Impossible de parser la plage: {plage_str}")


# Mapping Nom de jour → index weekday()
DAYS_MAP = {
    "Lundi": 0,
    "Mardi": 1,
    "Mercredi": 2,
    "Jeudi": 3,
    "Vendredi": 4,
    "Samedi": 5,
    "Dimanche": 6,
}


def find_occupied_slots(service, time_min, time_max, calendar_id="primary"):
    """
    Récupère les créneaux déjà occupés dans le calendrier Google
    entre time_min et time_max.
    Renvoie une liste de tuples (start_dt, end_dt).
    """
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    items = events_result.get("items", [])
    occupied = []

    for ev in items:
        sd = ev["start"].get("dateTime")
        ed = ev["end"].get("dateTime")
        if sd and ed:
            start_dt = datetime.datetime.fromisoformat(sd).astimezone(tz)
            end_dt = datetime.datetime.fromisoformat(ed).astimezone(tz)
            occupied.append((start_dt, end_dt))

    return occupied


def is_conflict(candidate_start, candidate_end, occupied):
    """
    Vérifie si le créneau [candidate_start, candidate_end] chevauche
    un créneau existant dans occupied.
    """
    for (s, e) in occupied:
        if candidate_start < e and candidate_end > s:
            return True
    return False


def try_schedule_for_client(
    client_row,
    occupied,
    meeting_duration_min=DEFAULT_MEETING_DURATION_MIN,
):
    """
    Essaie de trouver un créneau pour un client donné (dict Airtable 'fields').

    Utilise les champs :
        - 'Jours disponibles' (ex: "Mardi/Jeudi")
        - 'Plages horaires' (ex: "Entre 9h et 12h/Entre 14h et 18h")

    Renvoie (start_dt, end_dt) ou None si aucun créneau trouvé.
    """
    jours_raw = client_row.get("Jours disponibles")
    plages_raw = client_row.get("Plages horaires")

    if not jours_raw or not plages_raw:
        return None

    # Split sur / , ; etc.
    jours = re.split(r"[\/,;]", str(jours_raw))
    jours = [j.strip() for j in jours if j.strip()]

    plages = re.split(r"[\/,;]", str(plages_raw))
    plages = [p.strip() for p in plages if p.strip()]

    today = datetime.date.today()

    # début de la semaine courante (lundi)
    start_of_week = today - datetime.timedelta(days=today.weekday())

    for jour in jours:
        if jour not in DAYS_MAP:
            continue
        target_weekday = DAYS_MAP[jour]
        target_date = start_of_week + datetime.timedelta(days=target_weekday)

        # si déjà passé cette semaine → semaine suivante
        if target_date < today:
            target_date = target_date + datetime.timedelta(days=7)

        for plage in plages:
            try:
                (sh, sm), (eh, em) = parse_plage(plage)
            except Exception as e:
                print("Impossible de parser plage:", plage, e)
                continue

            candidate = datetime.datetime.combine(
                target_date, datetime.time(sh, sm, tzinfo=tz)
            )
            end_limit = datetime.datetime.combine(
                target_date, datetime.time(eh, em, tzinfo=tz)
            )

            while candidate + timedelta(minutes=meeting_duration_min) <= end_limit:
                candidate_end = candidate + timedelta(minutes=meeting_duration_min)
                if not is_conflict(candidate, candidate_end, occupied):
                    return candidate, candidate_end
                # pas dispo → on décale de 30 minutes
                candidate = candidate + timedelta(minutes=30)

    return None


def create_event(service, client_row, start_dt, end_dt, calendar_id="primary"):
    """
    Crée un événement Google Calendar pour un client.
    """
    email = client_row.get("Email")
    summary = f"Rendez-vous client : {client_row.get('Prénom','')} {client_row.get('Nom','')}".strip()

    event_body = {
        "summary": summary,
        "description": "RDV planifié automatiquement",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
    }

    if isinstance(email, str) and email.strip():
        event_body["attendees"] = [{"email": email.strip()}]

    created = (
        service.events()
        .insert(calendarId=calendar_id, body=event_body, sendUpdates="all")
        .execute()
    )
    return created


def schedule_appointments_from_airtable(
    airtable_api_key,
    airtable_base_id,
    airtable_table_id,
    calendar_id="primary",
    lookahead_days=DEFAULT_LOOKAHEAD_DAYS,
    meeting_duration_min=DEFAULT_MEETING_DURATION_MIN,
):
    """
    Fonction principale à appeler depuis ton main.

    - Récupère les événements existants dans le calendrier (pour éviter les conflits).
    - Récupère les clients dans Airtable.
    - Pour chaque client, cherche un créneau compatible avec ses dispo et le calendrier.
    - Crée un événement Google Calendar si un créneau est trouvé.
    """

    print("🔑 Authentification Google Calendar...")
    service = get_calendar_service()

    now = datetime.datetime.now(tz)
    time_min = now
    time_max = now + datetime.timedelta(days=lookahead_days)

    print("📅 Récupération des événements existants (conseiller)...")
    occupied = find_occupied_slots(service, time_min, time_max, calendar_id=calendar_id)
    print("   → Créneaux occupés récupérés :", len(occupied))

    print("📥 Récupération des clients depuis Airtable...")
    clients = fetch_airtable_records(
        airtable_api_key=airtable_api_key,
        airtable_base_id=airtable_base_id,
        airtable_table_id=airtable_table_id,
    )

    if not clients:
        print("   → Aucun client trouvé.")
        return

    print(f"   → {len(clients)} client(s) chargé(s).")

    for client in clients:
        prenom = client.get("Prénom", "")
        nom = client.get("Nom", "")
        print(f"\n👤 Client : {prenom} {nom}")

        slot = try_schedule_for_client(
            client,
            occupied,
            meeting_duration_min=meeting_duration_min,
        )

        if slot:
            start_dt, end_dt = slot
            print("   Créneau proposé :", start_dt, "-", end_dt)
            created = create_event(service, client, start_dt, end_dt, calendar_id)
            print("   ✅ Rendez-vous créé :", created.get("htmlLink"))
            # On ajoute ce créneau aux occupés pour respecter ce nouveau rdv
            occupied.append((start_dt, end_dt))
        else:
            print(
                f"   ❌ Aucun créneau libre trouvé pour ce client dans les {lookahead_days} prochains jours."
            )
