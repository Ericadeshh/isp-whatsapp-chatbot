
import logging
import os
from rasa.model_training import train  # pyright: ignore[reportMissingImports]

# Configure logging with emojis
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

MODEL_DIR = "models"

def train_rasa():
    logger.info("🛠️ Starting Rasa model training...")
    try:
        training_files = "."
        config = "config.yml"
        domain = "domain.yml"
        output = MODEL_DIR
        model_path = train(
            domain=domain,
            config=config,
            training_files=training_files,
            output=output,
            force_training=False
        )
        logger.info(f"✅ Rasa model trained successfully: {model_path}")
    except Exception as e:
        logger.error(f"❌ Error training Rasa model: {str(e)}")
        raise

def check_existing_models():
    if not os.path.exists(MODEL_DIR):
        logger.info(f"🆕 No models directory found. Creating {MODEL_DIR}...")
        os.makedirs(MODEL_DIR)
        return []

    models = [f for f in os.listdir(MODEL_DIR) if f.endswith(".tar.gz")]
    if models:
        logger.info(f"📊 Found {len(models)} existing models: {', '.join(models)}")
    else:
        logger.info("🆕 No existing models found")
    return models

if __name__ == "__main__":
    models = check_existing_models()
    if models:
        choice = input("Existing models found. Train new (y) or use existing (n)? [y/n]: ").strip().lower()
        if choice == 'y':
            train_rasa()
        else:
            logger.info("✅ Using existing models. No new training performed.")
    else:
        train_rasa()