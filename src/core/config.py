import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/etl_db")
API_KEY = os.getenv("API_KEY", "")
ETL_INTERVAL = int(os.getenv("ETL_INTERVAL", "3600"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API configuration
API_HOST = os.getenv("API_HOST", "http://jsonplaceholder.typicode.com")
CSV_URL = os.getenv("CSV_URL", "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv")

# Database connection pool settings
DB_POOL_MIN_SIZE = 5
DB_POOL_MAX_SIZE = 20
