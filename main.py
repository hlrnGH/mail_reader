from classifier import classify_crm_fields
from read_mails import retrieve_message_list, get_drive_service, get_gmail_service
from write_file import attach_drive_folders_to_messages
from send_to_airtable import add_record_to_airtable
from send_acknwoledgment_mail import send_acks_to_each

import os
from dotenv import load_dotenv

system_prompt = open("system_prompt_classifier.txt", "r", encoding="utf-8").read()

load_dotenv()
drive_id = os.getenv("GOOGLE_DRIVE_ID")
airtable_api_key = os.getenv("AIRTABLE_API_KEY")
airtable_base_id = os.getenv("AIRTABLE_BASE_ID")
airtable_table_id = os.getenv("AIRTABLE_TABLE_ID")

gmail_service = get_gmail_service()
drive_service = get_drive_service()

built_message_list = retrieve_message_list()
classified_messages = classify_crm_fields(built_message_list, system_prompt)

send_acks_to_each(gmail_service, classified_messages)

#print("messages list : ", classified_messages)

add_record_to_airtable(classified_messages, airtable_table_id, airtable_base_id, airtable_api_key)

attach_drive_folders_to_messages(drive_service, classified_messages, drive_id)

