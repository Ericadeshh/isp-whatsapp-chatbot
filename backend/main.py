# main.py
import logging
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
from db.database import Session, User

# Configure logging with emojis
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
    logger.info("📥 Received request to root endpoint")
    try:
        with Session() as session:
            user_count = session.query(User).count()
            logger.info(f"📊 Found {user_count} users in the database")
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
            existing_user = session.query(User).filter(User.phone == user.phone).first()
            if existing_user:
                logger.warning(f"⚠️ User with phone {user.phone} already exists")
                raise HTTPException(status_code=400, detail="Phone number already exists")
            new_user = User(phone=user.phone, name=user.name)
            session.add(new_user)
            session.commit()
            logger.info("✅ User added successfully")
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
        logger.info(f"✅ Rasa response: {rasa_response.json()}")
        return rasa_response.json()
    except Exception as e:
        logger.error(f"❌ Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))