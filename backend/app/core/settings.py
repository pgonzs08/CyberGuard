import os

from dotenv import load_dotenv

assert os.path.exists("./app/.env"), os.listdir("./app")

load_dotenv("./app/.env")


DEBUG = os.environ.get("DEBUG", "").strip().lower() in {"1", "true", "on", "yes"}
EXPIRATION_MINUTES = 3*60*24 #3 días
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")