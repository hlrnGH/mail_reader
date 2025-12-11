# Pierre Forbe Agent

## Aperçu du Projet

Pierre Forbe Agent est un système d’automatisation destiné à traiter les e-mails de prospects, structurer leurs informations, créer leurs dossiers, mettre à jour le CRM et lancer automatiquement les premières actions commerciales.
Le projet vise à accélérer l’acquisition et à rendre le suivi des prospects fiable, clair et automatisé.

---

# Ce qui nous a été demandé

## Critères de succès

Le projet est considéré comme réussi lorsque :

1. Le système transforme automatiquement un e-mail reçu en un lead structuré dans le CRM.
2. Un dossier propre par client est créé ou mis à jour dans Google Drive.
3. Les premiers e-mails sont envoyés automatiquement (accusé de réception, formulaires, etc.).
4. Le parcours des prospects est visible, clair et suivi (statuts, étapes, dates).
5. L’outil est suffisamment stable pour être utilisé par l’équipe immédiatement après le hackathon.

---


## Phase 1 — Réalisée

* Lecture automatique des e-mails non lus.
* Classification des e-mails par IA.
* Extraction des données pertinentes dans le contenu des e-mails.
* Création ou mise à jour du lead dans Airtable (CRM).
* Création automatique du dossier client dans Google Drive.
* Envoi automatique d’un e-mail d’accusé de réception personnalisé.
* Pipeline stable et fonctionnel de bout en bout.
* Envoi automatique d’un formulaire sécurisé au client dès qu’un collaborateur déclenche l’action depuis Airtable.




## Phase 2 — En cours / À venir

* Ajout automatique des fichiers PDF (pièces jointes) dans le dossier Drive du client.
* Introduction d’un module de machine learning pour détecter des documents valides ou frauduleux.
* Extraction automatique d’insights, données numériques et informations clés à partir des PDF, afin d’effectuer des calculs ou donner des indicateurs (revenus, ratios, informations financières ou administratives, etc.).

---

# Structure du Dossier

```
Pierre-Forbe-Agent/
│
├── main.py
├── read_mails.py
├── classifier.py
├── system_prompt_classifier.txt
│
├── create_client_drive.py
├── create_appointment.py
│
├── send_acknwoledgment_mail.py
├── acknowledgement_mail_template.txt
│
├── send_to_airtable.py
│
├── services.py
│
├── requirements.txt
├── .gitignore
└── (Logs, tokens et fichiers générés automatiquement)
```

---

# Description des fichiers

### main.py

Orchestre l’ensemble du pipeline :

1. lecture des e-mails,
2. classification,
3. extraction des données,
4. mise à jour Airtable,
5. création de dossier Drive,
6. géneration d'un formulaire avec documents à joindre,
7. envoi d’un e-mail automatique.


### read_mails.py

Connexion Gmail API et récupération des e-mails non lus.
Extraction des métadonnées et du contenu des messages.
Retourne des objets structurés pour traitement.

### classifier.py

Envoie le contenu de l'e-mail au modèle IA.
Classifie selon les règles décrites dans `system_prompt_classifier.txt`.
Renvoie la catégorie, les informations extraites et les niveaux de confiance.

### system_prompt_classifier.txt

Prompt détaillant :

* les catégories d’e-mails,
* les règles de classification,
* les informations à extraire,
* le format attendu en sortie.

### create_client_drive.py

Crée ou met à jour un dossier client dans Google Drive.
Structure des dossiers :
`/Clients/{Nom Prénom Email}`
Retourne l’ID du dossier Drive.
Base prévue pour l’ajout automatisé des PDF (Phase 2).

### create_appointment.py

Fichier préparé pour la création de rendez-vous automatisés.
Actuellement non utilisé mais prêt pour une future intégration calendrier.

### send_acknwoledgment_mail.py

Envoie un e-mail personnalisé d’accusé de réception grâce au template.
Utilise Gmail API pour l’envoi sécurisé.

### acknowledgement_mail_template.txt

Template textuel de l’e-mail d’accusé de réception.

### send_to_airtable.py

Gestion des interactions avec Airtable.
Upsert automatique : création ou mise à jour du lead.
Ajoute le statut, les données extraites.

### services.py

Fonctions utilitaires :

* gestion des services Google (Gmail, Drive),
* nettoyage du texte,
* transformation des données,
* parsing,
* logging standardisé,
* gestion des erreurs.

### requirements.txt

Liste complète des dépendances nécessaires.

---

# Prérequis Techniques

### Environnement

* Python 3.8 ou supérieur
* Pip installé
* Connexion internet fonctionnelle pour les APIs

### APIs requises

| API              | Fichier requis                        | Description                    |
| ---------------- | ------------------------------------- | ------------------------------ |
| Gmail API        | `credentials.json`                    | Identifiants OAuth Google      |
| Google Drive API | `credentials.json`                    | Même identifiants OAuth        |
| Token Google     | `token.json` (généré automatiquement) | Authentification persistante   |
| Airtable API     | `airtable_config.json`                | API key, Base ID, Table ID |

Exemple de fichier `airtable_config.json` :

```json
{
  "api_key": "CLE_AIRTABLE",
  "base_id": "BASEID",
  "table_id": "TABLE_ID"
}
```

---

# Installation

```
pip install -r requirements.txt
```

---

# Utilisation

```
python main.py
```

---

# Collaborateurs

* Rodrigue Hernais
* Setho Mariam
* Nassim BENCHIKH
* Harold Lerner
* Othniel Kadjo
