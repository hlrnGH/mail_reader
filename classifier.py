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

def classify_urgency(built_message_list):
    """
    Modifie built_message_list en place.
    Chaque élément doit être de la forme :
        {
            "id": msg_id,
            "sujet": subject,
            "urgence": "",
            "synthese": synthese,
        }
    Après appel, 'urgence' contient :
        Critique / Élevée / Modérée / Faible / Anodine
    """
    for msg in built_message_list:
        user_prompt = f"""Analyse ce message et choisis UNE SEULE classe d'urgence parmi :
                        Critique, Élevée, Modérée, Faible, Anodine.

                        Réponds uniquement par le nom de la classe.

                        Sujet :
                        {msg.get("sujet", "")}

                        Synthèse :
                        {msg.get("synthese", "")}
                        """

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # adapte si tu veux un autre modèle Groq
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )

        # On prend juste la première ligne, proprement
        label = completion.choices[0].message.content.strip().splitlines()[0]
        msg["urgence"] = label

    return built_message_list

built_message_list = retrieve_message_list()

#print("Total unread messages :", len(built_message_list))

classified_messages = classify_urgency(built_message_list)

print("Unread Messages :", len(classified_messages))

print("Sample classified message :", classified_messages[278]['urgence'])