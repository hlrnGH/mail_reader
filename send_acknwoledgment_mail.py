import base64
from email.message import EmailMessage
from googleapiclient.errors import HttpError


def send_ack_email(gmail_service, to_email: str):
    """
    Envoie un mail d'accusé de réception à `to_email` via l'API Gmail.
    Utilise le compte associé aux credentials (userId='me').
    """
    if not to_email:
        print("[SKIP] Pas d'email fourni, envoi annulé.")
        return None

    # Construction du message
    msg = EmailMessage()
    msg["To"] = to_email
    msg["Subject"] = "Nous avons bien reçu votre demande"

    msg.set_content(
        """Bonjour,

Nous avons bien reçu votre demande, et nous vous remercions de l’intérêt que vous portez à Paul Forbe.

Un conseiller de notre équipe va vous contacter très prochainement afin d’échanger avec vous sur votre projet et vos besoins.

En attendant cet échange, aucune action n’est requise de votre côté.
Vous pouvez bien entendu répondre à cet email si vous avez la moindre question.

À très bientôt,

L’équipe Paul Forbe
"""
    )

    # Encodage base64 URL-safe attendu par Gmail
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    body = {"raw": raw}

    try:
        sent = gmail_service.users().messages().send(
            userId="me",
            body=body
        ).execute()
        print(f"[OK] Mail envoyé à {to_email} (id: {sent.get('id')})")
        return sent
    except HttpError as e:
        print(f"[ERREUR] Échec d'envoi à {to_email} : {e}")
        return None

from email.utils import parseaddr

def send_acks_to_each(gmail_service, classified_mailset):
    """
    Parcourt la liste classified_mailset, récupère le champ 'from',
    en extrait l'adresse e-mail, et envoie l'accusé de réception
    à chaque expéditeur.

    - gmail_service : service Gmail (build("gmail", "v1", credentials=creds))
    - classified_mailset : liste de dicts (tes messages enrichis)
    """
    for msg in classified_mailset:
        raw_from = msg.get("from") or msg.get("From") or ""
        name, email_addr = parseaddr(raw_from)
        email_addr = (email_addr or "").strip()

        if not email_addr:
            print(f"[SKIP] Pas d'adresse e-mail exploitable dans 'from' pour id={msg.get('id')}")
            continue

        # Petit filtre pour éviter de spammer Google et les no-reply
        if "no-reply@" in email_addr or "accounts.google.com" in email_addr:
            print(f"[SKIP] Adresse système / no-reply : {email_addr}")
            continue

        print(f"[INFO] Envoi de l'accusé de réception à {email_addr} (from='{raw_from}')")
        send_ack_email(gmail_service, email_addr)
