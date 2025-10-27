from dotenv import load_dotenv
import os

load_dotenv()

API_URL = 'https://api.ynab.com/v1'
API_TOKEN = os.getenv('API_TOKEN')
START_DATE = '2025-01-01'