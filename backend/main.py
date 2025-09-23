import logging
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from twilio.twiml.messaging_response import MessagingResponse  # pyright: ignore[reportMissingImports]
import requests
from db.database import Session, User

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ISP WhatsApp Chatbot")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting FastAPI server...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down FastAPI server...")

@app.get("/")
async def read_root():
    logger.info("📥 Received root request")
    try:
        with Session() as session:
            user_count = session.query(User).count()
            logger.info(f"📊 Found {user_count} users")
            return {"message": "ISP Chatbot Backend", "user_count": user_count}
    except Exception as e:
        logger.error(f"❌ Error querying users: {str(e)}")
        return {"message": "ISP Chatbot Backend", "error": str(e)}

class UserCreate(BaseModel):
    phone: str
    name: str

@app.post("/add-user")
async def add_user(user: UserCreate):
    logger.info(f"➕ Adding user: {user.name} ({user.phone})")
    try:
        with Session() as session:
            if session.query(User).filter(User.phone == user.phone).first():
                logger.warning(f"⚠️ Phone {user.phone} exists")
                raise HTTPException(status_code=400, detail="Phone number already exists")
            new_user = User(phone=user.phone, name=user.name)
            session.add(new_user)
            session.commit()
            logger.info("✅ User added")
            return {"message": "User created", "user_id": new_user.id}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error adding user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class ChatMessage(BaseModel):
    text: str

@app.post("/chat")
async def chat(message: ChatMessage):
    logger.info(f"💬 Received message: {message.text}")
    try:
        rasa_response = requests.post("http://localhost:5005/webhooks/rest/webhook", json={"sender": "user", "message": message.text})
        rasa_response.raise_for_status()
        response_data = rasa_response.json()
        if not response_data:
            logger.warning("⚠️ Empty Rasa response")
            return [{"recipient_id": "user", "text": "Sorry, I didn't understand. Try saying 'check my bill', 'report outage', 'signup', or 'goodbye'. 😊"}]
        logger.info(f"✅ Rasa response: {response_data}")
        return response_data
    except requests.RequestException as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.form()
    message = data.get("Body")
    sender = data.get("From")
    logger.info(f"📱 WhatsApp message from {sender}: {message}")
    try:
        rasa_response = requests.post("http://localhost:5005/webhooks/rest/webhook", json={"sender": sender, "message": message})
        rasa_response.raise_for_status()
        response_data = rasa_response.json()
        response_text = response_data[0]["text"] if response_data else "Sorry, I didn't understand. Try saying 'check my bill', 'report outage', 'signup', or 'goodbye'. 😊"
        logger.info(f"✅ WhatsApp response: {response_text}")
        twiml = MessagingResponse()
        twiml.message(response_text)
        return Response(content=str(twiml), media_type="application/xml")
    except requests.RequestException as e:
        logger.error(f"❌ WhatsApp error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))