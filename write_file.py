from classifier import classify_urgency
from read_mails import retrieve_message_list

from dotenv import load_dotenv
from groq import Groq

import os

# get api key from .env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def write_classified_messages_in_sheet(classified_messages):

#def write_classified_messages_in_sheet(classified_messages):
