import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/etl_db")
API_KEY = os.getenv("API_KEY", "")
ETL_INTERVAL = int(os.getenv("ETL_INTERVAL", "3600"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API configuration
API_HOST = os.getenv("API_HOST", "http://jsonplaceholder.typicode.com")
CSV_PATH = os.getenv("CSV_PATH", "./data/sample.csv")  # Local file path instead of URL
