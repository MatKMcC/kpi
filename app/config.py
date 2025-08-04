from dotenv import load_dotenv
import os

load_dotenv()

TOSHL_API_URL = 'https://api.toshl.com'
API_TOKEN = os.getenv('API_TOKEN')
START_DATE = '2025-01-01'