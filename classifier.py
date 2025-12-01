from read_mails import retrieve_message_list

built_message_list = retrieve_message_list()

print("Unread Messages :", len(built_message_list))