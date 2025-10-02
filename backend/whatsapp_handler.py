from fastapi import Request, Response, HTTPException
import logging
import requests
from twilio.twiml.messaging_response import MessagingResponse
from db.database import Log
from datetime import datetime

logger = logging.getLogger(__name__)

async def handle_whatsapp_webhook(request: Request):
    logger.info("📱 WhatsApp webhook triggered")
    try:
        data = await request.form()
        message = data.get("Body", "").lower()
        sender = data.get("From")
        logger.info(f"📱 WhatsApp message from {sender}: {message}")
        
        rasa_response = requests.post("http://localhost:5005/webhooks/rest/webhook", json={"sender": sender, "message": message})
        rasa_response.raise_for_status()
        response_data = rasa_response.json()
        response_text = response_data[0]["text"] if response_data else "🚫 Sorry, I didn’t understand. Try again! 😔"

        logger.info(f"✅ WhatsApp response: {response_text}")
        twiml = MessagingResponse()
        twiml.message(response_text)
        with open("whatsapp_log.txt", "a", encoding="utf-8") as log_file:  # Added encoding="utf-8"
            log_file.write(f"{datetime.now()}: {sender} - {message} - {response_text}\n")
        return Response(content=str(twiml), media_type="application/xml")
    except requests.RequestException as e:
        logger.error(f"❌ WhatsApp error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))