
import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def test_chat(message):
    logger.info(f"💬 Sending message: {message}")
    try:
        response = requests.post(
            "http://127.0.0.1:8000/chat",
            json={"text": message},
            headers={"Content-Type": "application/json"}
        )
        logger.info(f"✅ Response: {response.json()}")
        return response.json()
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    while True:
        message = input("Enter your message (or 'exit' to quit): ").strip()
        if message.lower() == 'exit':
            logger.info("👋 Exiting chat test")
            break
        test_chat(message)
