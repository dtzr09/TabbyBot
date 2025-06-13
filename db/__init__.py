from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from db.models import Base

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Base.metadata.drop_all(bind=engine)  # Danger: deletes all tables (For development only)
Base.metadata.create_all(bind=engine)
