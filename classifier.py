import os

from dotenv import load_dotenv
from groq import Groq 

from read_mails import retrieve_message_list


# get api key from .env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# initialize system prompt
SYSTEM_PROMPT = """
Tu es un classificateur d'e-mails pour un support interne.

Ton rôle est d'attribuer UNE SEULE classe d'urgence à chaque message, parmi :

- Critique : impact majeur, opération impossible, nécessite intervention immédiate
- Élevée : impact important, forte gêne, traitement prioritaire
- Modérée : gêne notable mais non bloquante
- Faible : problème mineur
- Anodine : demande simple, aucun enjeu d’urgence

Règles importantes :
- Réponds UNIQUEMENT par le nom de la classe : "Critique", "Élevée", "Modérée", "Faible" ou "Anodine".
- Ne rajoute ni phrase, ni justification, ni ponctuation.
"""


built_message_list = retrieve_message_list()

print("Total unread messages :", len(built_message_list))

#classified_messages = classify_urgency(built_message_list)

#print("Unread Messages :", len(classified_messages))

#print("Sample classified message :", classified_messages[278]['urgence'])