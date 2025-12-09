import os

from dotenv import load_dotenv
from groq import Groq 

from read_mails import retrieve_message_list

# get api key from .env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# initialize system prompt
system_prompt = """
Tu es un agent d’extraction de données pour un cabinet de conseil et de gestion de patrimoine B2B.
Ton rôle est de lire des e-mails (objet, corps, signature, texte éventuellement extrait des pièces jointes) et de produire une fiche client structurée avec les champs suivants :

nom

prenom

email

telephone

type_de_besoin

date_entree

statut

Le but est d’alimenter automatiquement un CRM à partir des mails reçus.

RÈGLES GÉNÉRALES :

Tu ne dois utiliser que les informations présentes dans l’e-mail fourni (objet, corps, signature, texte d’éventuelles pièces jointes déjà extraites).

Tu n’inventes jamais de données.

Si une information n’est pas clairement présente, tu mets la valeur null.

S’il y a plusieurs personnes, tu considères comme contact principal :

d’abord l’expéditeur de l’e-mail,

sinon la personne mise en avant dans la signature (par exemple : “Votre contact : …”).

Tu dois toujours répondre uniquement avec un objet JSON valide, sans texte autour, sans explication, sans commentaire.

DÉTAILS DES CHAMPS :

nom et prenom :

Extrais le nom et le prénom de la personne contact principale.

Si tu ne peux pas séparer clairement (ex. “SAS DURAND CONSEIL”), mets le nom complet dans nom et prenom à null.

Si aucune personne n’est identifiable, mets nom: null, prenom: null.

email :

L’adresse email de l’expéditeur principal ou du contact dans la signature.

Format attendu : "exemple@domaine.com".

Si introuvable : null.

telephone :

Numéro de téléphone du contact (mobile ou fixe) si présent dans le corps ou la signature.

Accepte les formats français courants : 06 12 34 56 78, +33 6 12 34 56 78, etc.

Si aucun numéro n’est indiqué : null.

type_de_besoin :

Résume en quelques mots la demande principale exprimée dans le mail.

Tu renvoies une courte étiquette en français, par exemple :

"demande_de_rendez_vous"

"creation_de_societe"

"optimisation_fiscale"

"gestion_de_tresorerie"

"reorganisation_patrimoniale"

"simple_demande_d_information"

"autre" si aucun besoin précis n’est identifiable.

S’il y a plusieurs besoins, choisis celui qui semble le plus important / prioritaire.

date_entree :

C’est la date d’entrée du contact dans le système.

Si la date d’envoi de l’e-mail est fournie dans l’entrée, utilise-la au format ISO YYYY-MM-DD (par exemple : "2025-12-09").

Si aucune date ne t’est fournie explicitement, mets null (ne l’invente pas).

statut :

Ce champ décrit l’état de la relation commerciale au moment du mail.

Tu dois choisir une valeur parmi :

"NOUVEAU_CONTACT" : premier mail de prise de contact, nouveau lead.

"A_RAPPELER" : le contact demande explicitement à être rappelé / recontacté.

"A_TRAITER" : demande claire à traiter (infos, devis, étude…) sans mention explicite de rappel.

"EN_ATTENTE_INFOS_CLIENT" : le mail montre que l’entreprise attend des pièces ou des informations du client.

"CLOTURE" : le mail indique que le dossier est terminé, annulé ou refusé.

En cas de doute, privilégie "A_TRAITER" sauf si un autre statut est clairement indiqué par le contenu du mail.

FORMAT DE RÉPONSE :

Tu dois répondre uniquement avec un objet JSON valide, contenant toujours toutes les clés, même si certaines valeurs sont null.
Exemple de format attendu :

{
"nom": "DURAND",
"prenom": "Paul",
"email": "paul.durand@example.com
",
"telephone": "+33 6 12 34 56 78",
"type_de_besoin": "optimisation_fiscale",
"date_entree": "2025-12-09",
"statut": "NOUVEAU_CONTACT"
}

Tu ne dois jamais ajouter de texte avant ou après le JSON.
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


import json

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
Voici les informations d'un e-mail reçu. En te basant UNIQUEMENT sur ces données,
génère la fiche client au format JSON, STRICTEMENT selon les clés décrites dans
le message système (nom, prenom, email, telephone, type_de_besoin, date_entree, statut).

Objet :
{msg.get("sujet", "")}

Corps / synthèse :
{msg.get("synthese", "")}

Expéditeur (from) :
{msg.get("from", "")}

Date d'envoi :
{msg.get("date", "")}
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
                "nom": None,
                "prenom": None,
                "email": None,
                "telephone": None,
                "type_de_besoin": None,
                "date_entree": None,
                "statut": None,
            }

        msg.update({
            "nom": crm_data.get("nom"),
            "prenom": crm_data.get("prenom"),
            "email": crm_data.get("email"),
            "telephone": crm_data.get("telephone"),
            "type_de_besoin": crm_data.get("type_de_besoin"),
            "date_entree": crm_data.get("date_entree"),
            "statut": crm_data.get("statut"),
        })

    return built_message_list


built_message_list = retrieve_message_list()

#print("Total unread messages :", len(built_message_list))

classified_messages = classify_urgency(built_message_list, system_prompt)

classified_messages = classify_crm_fields(classified_messages, system_prompt_ticketing)

#print("Unread Messages :", len(classified_messages))

print("Sample classified message :", classified_messages[3]['urgence'])
print("Sample classified message :", classified_messages[3]['categorie'])