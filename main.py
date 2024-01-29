import requests
import json
from pprint import pprint
from datetime import datetime

API_VERSION = "v18.0"

class PageMessenger():
    def __init__(self, page_id, access_token):
        self.page_id = page_id
        # Page Access Token  [EXPIRES AFTER ABOUT TWO HOURS!]
        self.access_token = access_token

    def _filter_conversations_by_time(self, data, start, end):
        filtered_data = []
        for conversation in data:
            updated_time_str = conversation.get("updated_time")
            
            # Convert the updated_time string to a datetime object
            updated_time = datetime.strptime(updated_time_str, "%Y-%m-%dT%H:%M:%S%z")

            # Check if the conversation's updated_time falls within the specified range
            if start is None or (updated_time.hour >= start and updated_time.hour <= end):
                filtered_data.append(conversation)

        return filtered_data
    

    def _filter_messages_by_time(self, messages, start, end):
        filtered_messages = []

        for message in messages:
            created_time_str = message.get("created_time")
            created_time = datetime.strptime(created_time_str, "%Y-%m-%dT%H:%M:%S%z")

            if start is None or (created_time.hour >= start and created_time.hour <= end):
                filtered_messages.append(message)

        return filtered_messages


    def get_conversations(self, start=None, end=None):

        url = f"https://graph.facebook.com/{API_VERSION}/{self.page_id}/conversations?platform=messenger&access_token={self.access_token}"

        try:
            print("Fetching conversations...")
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error in api call: {e}")
        
        # Get a list of all conversations currently in the page Messenger inbox
        all_conversations_data = response.json().get("data", [])

        # Declare dictionary that will house final output
        final_output = dict()

        if start is not None or end is not None:
            filtered_conversations_data = self._filter_conversations_by_time(all_conversations_data, start, end)

            # Hit endpoint to fetch all messages for each (filtered/unfiltered) conversation
            for conversation in filtered_conversations_data:
                messages_from_conversation = []
                url = f"https://graph.facebook.com/{API_VERSION}/{conversation['id']}?fields=messages&access_token={self.access_token}"
                print("Fetching messages...")
                response = requests.get(url)
                messages_data = response.json()

                # Fetch actual content + details for each message
                for message in messages_data['messages']['data']:
                    message_id = message['id']
                    url = f"https://graph.facebook.com/{API_VERSION}/{message_id}?fields=id,created_time,from,to,message,attachments&access_token={self.access_token}"

                    try: 
                        response = requests.get(url)
                        response.raise_for_status()
                        print("Fetching individual message content...")
                    except requests.exceptions.RequestException as e:
                        print(f"Error in api call: {e}")

                    data = response.json()
                    messages_from_conversation.append(data)

                    time_filtered_messages = self._filter_messages_by_time(messages_from_conversation, start, end)

                final_output[conversation['id']] = time_filtered_messages

            print(json.dumps(final_output, indent=2))

        else:
            print(json.dumps(data, indent=2))
            return data


    def reply_conversation(self, user_id, message_content):

        url = f"https://graph.facebook.com/{API_VERSION}/{self.page_id}/messages?access_token={self.access_token}"

        headers = {
            "Content-Type": "application/json"
        }

        data = json.dumps({
            "recipient": {
                "id": f"{user_id}"
            },
            "messaging_type": "RESPONSE",
            "message": {
                "text":f"{message_content}"
            }
        })

        response = requests.post(url, headers=headers, data=data)
        print(json.dumps(response.json(), indent=2))


    def generate_new_access_token(self):
        app_id = "1077010686869361"
        client_secret = "00675b1043791d3dfefafc0d2639cc7d"

        # Get long-lived user access token 
        url = f"https://graph.facebook.com/{API_VERSION}/oauth/access_token?grant_type=fb_exchange_token&client_id={app_id}&client_secret={client_secret}&fb_exchange_token={self.access_token}"
        
        try: 
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error in api call: {e}")

        new_user_access_token = response.json()['access_token']
        print("New User Access Token: ", new_user_access_token)

        # Get long lived page access token
        url = f"https://graph.facebook.com/{API_VERSION}/122104683908167192/accounts?access_token={new_user_access_token}"
        
        try: 
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error in api call: {e}")

        new_page_access_token = response.json()['data'][0]['access_token']
        print("New Page Access Token: ", new_page_access_token)

        self.access_token = new_page_access_token

import config
my_token = config.Access_Token
page_id = config.page_id
    
messenger = PageMessenger(page_id, my_token)    

messenger.get_conversations(0, 23)
# messenger.reply_conversation(6514491511984465, "Alright buddy. Your ticket has been created.")
# messenger.generate_new_access_token()