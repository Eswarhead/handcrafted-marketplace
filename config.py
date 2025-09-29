import os
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/handcrafted')
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
CLOUDINARY_URL = os.getenv('CLOUDINARY_URL', None)
RZP_KEY_ID = os.getenv('RZP_KEY_ID', '')
RZP_KEY_SECRET = os.getenv('RZP_KEY_SECRET', '')

# API prefix (optional)
API_PREFIX = '/api'
