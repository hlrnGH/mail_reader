import os

from dotenv import load_dotenv
from groq import Groq 

from read_mails import retrieve_message_list

# get api key from .env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# initialize system prompt
system_prompt = """
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

system_prompt_ticketing = """
Tu es un système de classification de tickets de support.

Ton rôle est de classer chaque message dans UNE SEULE catégorie de ticket parmi :

- Problème technique informatique
- Demande administrative
- Problème d’accès / authentification
- Demande de support utilisateur
- Bug ou dysfonctionnement d’un service

Définitions rapides :
- Problème technique informatique : soucis liés au matériel, logiciel, réseau, configuration, installation, performance, pannes informatiques en général.
- Demande administrative : questions de facturation, contrat, justificatif, changement d’adresse, inscription, documents officiels, RH, etc.
- Problème d’accès / authentification : login impossible, mot de passe oublié, compte verrouillé, droits d’accès manquants, SSO, etc.
- Demande de support utilisateur : besoin d’aide pour utiliser un outil, comprendre une fonctionnalité, accompagnement, formation, mode d’emploi.
- Bug ou dysfonctionnement d’un service : une fonctionnalité qui ne marche pas comme prévu dans une application ou un service (erreur, comportement inattendu, résultats incorrects).

Règles :
- Choisis UNE SEULE catégorie par message.
- Réponds UNIQUEMENT par le nom exact d’une des catégories ci-dessus.
- Ne rajoute ni phrase, ni explication, ni ponctuation.
"""

def classify_urgency(built_message_list,system_prompt):
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
            model="llama-3.1-8b-instant",  
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )

        label = completion.choices[0].message.content.strip().splitlines()[0]
        msg["urgence"] = label

    return built_message_list


def classify_tickets_categories(classified_messages,system_prompt):

    for msg in classified_messages:
        user_prompt = f"""Voici un message utilisateur. 
                    Classe-le dans UNE SEULE catégorie parmi :
                    - Problème technique informatique
                    - Demande administrative
                    - Problème d’accès / authentification
                    - Demande de support utilisateur
                    - Bug ou dysfonctionnement d’un service

                    Réponds uniquement par le nom exact de la catégorie.

                    Sujet :
                    {msg.get("sujet", "")}

                    Synthèse :
                    {msg.get("synthese", "")}

                    Urgence :
                    {msg.get("urgence", "")}
                    """

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # même modèle Groq que pour l'urgence
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )

        label = completion.choices[0].message.content.strip().splitlines()[0]
        msg["categorie"] = label

    return classified_messages


built_message_list = retrieve_message_list()

#print("Total unread messages :", len(built_message_list))

classified_messages = classify_urgency(built_message_list, system_prompt)

classified_messages = classify_tickets_categories(classified_messages, system_prompt_ticketing)

#print("Unread Messages :", len(classified_messages))

print("Sample classified message :", classified_messages[278]['urgence'])
print("Sample classified message :", classified_messages[278]['categorie'])