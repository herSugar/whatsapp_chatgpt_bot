from fastapi import FastAPI, Request
from pydantic import BaseModel
import json
import requests
import os

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_verify_token")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")  # dari Meta
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Endpoint untuk verifikasi webhook dari Meta
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))
    return {"status": "invalid verify token"}

# Endpoint untuk menerima pesan dari WhatsApp
@app.post("/webhook")
async def receive_message(data: dict):
    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        messages = value.get("messages")
        
        if messages:
            message = messages[0]
            text = message['text']['body']
            sender = message['from']

            # Kirim ke OpenAI
            openai_response = chatgpt_reply(text)
            send_whatsapp_message(sender, openai_response)

    except Exception as e:
        print("Error:", e)
    return {"status": "ok"}

# Fungsi balas ke WhatsApp
def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    requests.post(url, headers=headers, json=payload)

# Fungsi call ChatGPT
# def chatgpt_reply(user_message):
#     headers = {
#         "Authorization": f"Bearer {OPENAI_API_KEY}",
#         "Content-Type": "application/json"
#     }
#     data = {
#         "model": "gpt-4",
#         "messages": [
#             {"role": "user", "content": user_message}
#         ]
#     }
#     response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
#     reply = response.json()
#     return reply['choices'][0]['message']['content']
def gemini_reply(user_message):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": user_message}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    result = response.json()

    try:
        return result['candidates'][0]['content']['parts'][0]['text']
    except:
        print("Gemini response error:", result)
        return "Maaf, saya tidak bisa membalas saat ini."
