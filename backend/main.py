import logging
import requests  # Added this import
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from whatsapp_handler import handle_whatsapp_webhook
from db.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('isp_chatbot')
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(stream_handler)

app = FastAPI(title="Bayzinet Customer Care Chatbot")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting FastAPI server...")
    logger.debug("🧪 Testing DBHandler on startup")
    init_db()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down FastAPI server...")

@app.get("/")
async def read_root():
    logger.info("📥 Received root request")
    from db.database import DBHandler
    db_handler = DBHandler()
    users = db_handler.get_users()
    logger.info(f"📊 Found {len(users)} users")
    return {"message": "Bayzinet Customer Care Backend", "user_count": len(users)}

class UserCreate(BaseModel):
    phone: str
    name: str

@app.post("/add-user")
async def add_user(user: UserCreate):
    logger.info(f"➕ Adding user: {user.name} ({user.phone})")
    try:
        from db.database import Session
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
            return [{"recipient_id": "user", "text": "🚫 Sorry, I didn’t understand. Try again! 😔"}]
        logger.info(f"✅ Rasa response: {response_data}")
        return response_data
    except requests.RequestException as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    return await handle_whatsapp_webhook(request)