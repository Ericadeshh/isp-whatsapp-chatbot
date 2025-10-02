import logging
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from datetime import datetime
from dotenv import load_dotenv
import os
import re

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

MYSQL_USER = os.getenv("MYSQL_USER", "Ericadesh")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "404-found-#")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "isp_chatbot")
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    phone = Column(String(20), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending")

class Outage(Base):
    __tablename__ = "outages"
    id = Column(Integer, primary_key=True)
    description = Column(String(200), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    service = Column(String(50), nullable=True)  # e.g., "billing", "outage"
    username = Column(String(50), nullable=True)  # e.g., user’s name
    phone_no = Column(String(20), nullable=True)  # e.g., "0712345678"

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)

class DBHandler:
    def __init__(self):
        self.engine, self.Session = init_db()

    def get_users(self):
        with self.Session() as session:
            return session.query(User).all()

def init_db():
    try:
        initial_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}"
        engine = create_engine(initial_url, echo=False)
        logger.info("🔌 Attempting connection to MySQL server...")

        with engine.connect() as conn:
            result = conn.execute(text(f"SHOW DATABASES LIKE '{MYSQL_DATABASE}'"))
            if result.fetchone():
                logger.info(f"✅ Database '{MYSQL_DATABASE}' exists. Loading existing data.")
            else:
                logger.info(f"🆕 Database '{MYSQL_DATABASE}' does not exist. Creating afresh...")
                conn.execute(text(f"CREATE DATABASE {MYSQL_DATABASE}"))
                logger.info(f"✅ Database '{MYSQL_DATABASE}' created successfully.")

        engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        inspector = inspect(engine)
        logger.info("🔌 Connected to MySQL server successfully.")

        tables = {"users": User, "bills": Bill, "outages": Outage, "logs": Log, "payments": Payment}
        for table_name, model in tables.items():
            if inspector.has_table(table_name):
                logger.info(f"📊 Table '{table_name}' exists. Verifying columns...")
                existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
                expected_columns = set(model.__table__.columns.keys())
                if existing_columns == expected_columns:
                    logger.info(f"✅ Table '{table_name}' has correct columns. Checking rows...")
                else:
                    logger.warning(f"⚠️ Table '{table_name}' has incorrect columns. Expected: {expected_columns}, Found: {existing_columns}. Recreating afresh...")
                    model.__table__.drop(engine)
                    model.__table__.create(engine)
                    logger.info(f"✅ Table '{table_name}' recreated with correct columns.")
            else:
                logger.info(f"🆕 Table '{table_name}' does not exist. Creating afresh...")
                model.__table__.create(engine)
                logger.info(f"✅ Table '{table_name}' created successfully.")

            with engine.connect() as conn:
                with conn.begin():
                    row_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                    if row_count > 0:
                        logger.info(f"📈 Table '{table_name}' has {row_count} rows. Using existing data.")
                    elif table_name != "logs":
                        logger.info(f"🆕 Table '{table_name}' is empty. Inserting sample data afresh...")
                        if table_name == "users":
                            conn.execute(text("INSERT INTO users (phone, name) VALUES ('0741091661', 'Eric Adegu')"))
                        elif table_name == "bills":
                            conn.execute(text("INSERT INTO bills (user_id, amount, due_date, status) VALUES (1, 1000.0, '2025-10-01', 'pending')"))
                        elif table_name == "outages":
                            conn.execute(text("INSERT INTO outages (description, start_time) VALUES ('Sample outage', '2025-09-19')"))
                        elif table_name == "payments":
                            conn.execute(text("INSERT INTO payments (user_id, amount, date) VALUES (1, 500.0, '2025-09-15')"))
                        logger.info(f"✅ Sample data inserted into '{table_name}' successfully.")

        Session = sessionmaker(bind=engine)
        logger.info("✅ Database initialization completed successfully.")
        return engine, Session

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise

engine, Session = init_db()