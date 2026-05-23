import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    DATABASE_PATH = os.getenv("DATABASE_PATH")

    DEBUG = os.getenv("DEBUG", "false").lower() == "true"