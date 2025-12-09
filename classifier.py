import os
import json

from dotenv import load_dotenv
from groq import Groq 

from read_mails import retrieve_message_list

# get api key from .env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# initialize system prompt
system_prompt = open("system_prompt_classifier.txt", "r", encoding="utf-8").read()


def classify_crm_fields(built_message_list, system_prompt):
    """
    Pour chaque message de built_message_list, appelle le LLM avec system_prompt
    (qui définit les champs : nom, prenom, email, telephone, type_de_besoin,
    date_entree, statut) et enrichit le dict du message avec ces clés.

    Format attendu pour chaque élément de built_message_list avant appel :
        {
            "id": ...,
            "sujet": ...,
            "synthese": ...,
            # optionnel mais utile si tu les as :
            "from": "...",
            "date": "2025-12-09 10:15:00",
        }

    Après appel, chaque msg est enrichi avec :
        "nom", "prenom", "email", "telephone",
        "type_de_besoin", "date_entree", "statut"
    """

    for msg in built_message_list:
        user_prompt = f"""
Voici un e-mail à analyser. Les informations sont fournies ci-dessous de manière structurée.

[EMAIL]
id: {msg.get("id", "")}
sujet: {msg.get("sujet", "")}
from: {msg.get("from", "")}
date: {msg.get("date", "")}
synthese: {msg.get("synthese", "")}

texte_complet:
{msg.get("texte_complet", "")}
[/EMAIL]

À partir EXCLUSIVEMENT de ces informations, produis un objet JSON valide contenant
STRICTEMENT les clés suivantes :

"Titre du bien",
"Référence",
"Ville du bien",
"Prix du bien",
"Référent",
"Prénom",
"Nom",
"Email",
"Téléphone",
"Adresse",
"Ville",
"Code postal",
"Département",
"Est propriétaire",
"Achète pour",
"Bien recherché",
"Budget d achat",
"A un dossier de financement",
"Délai d achat",
"Secteurs de recherche",
"Est intéressé par du programme neuf",
"Jours disponibles",
"Plages horaires"

Les règles détaillées pour chaque champ sont définies dans le message système.
Tu n’inventes aucune donnée : si une information n’est pas clairement présente
dans le texte, tu mets null (ou [] pour les listes).

Réponds UNIQUEMENT avec l'objet JSON, sans aucun texte autour.
"""



        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )

        raw_content = completion.choices[0].message.content.strip()

        # Tentative de parse du JSON renvoyé par le modèle
        try:
            crm_data = json.loads(raw_content)
        except json.JSONDecodeError:
            # Sécurité minimale : si le modèle foire, on met tout à null au lieu de crasher
            crm_data = {
                "Titre du bien" : None, 
                "Référence" : None,
                "Ville du bien" : None, 
                "Prix du bien" : None, 
                "Référent" : None, 
                "Prénom" : None, 
                "Nom" : None, 
                "Email" : None, 
                "Téléphone" : None, 
                "Adresse" : None, 
                "Ville" : None, 
                "Code postal" : None, 
                "Département" : None, 
                "Est propriétaire": None, 
                "Achète pour" :None , 
                "Bien recherché" :None , 
                "Budget d achat" :None , 
                "A un dossier de financement" :None , 
                "Délai d achat" : None, 
                "Secteurs de recherche" : None, 
                "Est intéressé par du programme neuf" :None , 
                "Jours disponibles" : [], 
                "Plages horaires" : []
            }

        msg.update(crm_data)

    return built_message_list


built_message_list = retrieve_message_list()

#print("Total unread messages :", len(built_message_list))

classified_messages = classify_crm_fields(built_message_list, system_prompt)

#print("Unread Messages :", len(classified_messages))

print("Sample classified message :", classified_messages[5]['Prénom'], classified_messages[5]['Nom'])
#print("Sample classified message :", classified_messages[3]['categorie'])

#print("System prompt used :", system_prompt)