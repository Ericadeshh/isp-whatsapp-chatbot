import requests
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def test_chat(message):
    logger.info(f"💬 Sending message: {message}")
    try:
        # Wait briefly to ensure server is ready
        time.sleep(1)
        response = requests.post(
            "http://127.0.0.1:8000/chat",
            json={"text": message},  # Matches ChatMessage model in main.py
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()  # Raise an error for bad status codes
        logger.info(f"✅ Response: {response.json()}")
        return response.json()
    except requests.exceptions.ConnectionError:
        logger.error("❌ Error: FastAPI server (http://127.0.0.1:8000) is not running. Start it with 'uvicorn main:app --reload --port 8000'.")
        raise
    except requests.exceptions.Timeout:
        logger.error("❌ Error: Request to FastAPI server timed out. Check if the server is responsive.")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ Error: HTTP Error {e.response.status_code} - {e.response.text}")
        raise
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