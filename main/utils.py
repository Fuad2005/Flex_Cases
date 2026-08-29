import os
import requests

# def send_whatsapp_message(recipient_number, text_message):
#     """
#     Sends a standard text message to a WhatsApp user.
#     recipient_number format: "994702148626" (country code + number without + or spaces)
#     """
#     phone_id = os.getenv("PHONE_NUMBER_ID")
#     token = os.getenv("WHATSAPP_TOKEN")
    
#     url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "messaging_product": "whatsapp",
#         "recipient_type": "individual",
#         "to": recipient_number,
#         "type": "text",
#         "text": {
#             "preview_url": False,
#             "body": text_message
#         }
#     }
    
#     response = requests.post(url, json=payload, headers=headers)
#     return response.json()