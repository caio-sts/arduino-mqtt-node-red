from twilio.rest import Client
import os, json

def notify(alert_msg):
    account_sid = os.environ['account_sid']
    auth_token = os.environ['auth_token']
    client = Client(account_sid, auth_token)
  
    with open('Cliente.json', "r+") as f:
        data = json.load(f)
        telefone = data["telefone"]
  
    client.messages.create(from_='whatsapp:+14155238886',
                           body=alert_msg,
                           to=f'whatsapp:{telefone}')
