import os
import sys

NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]
MONGO_URI = os.environ["MONGO_URI"]
DEBUG = os.environ.get("DEBUG", "").strip().lower() in {"1", "true", "on", "yes"}
EXPIRATION_MINUTES = 3*60*24 #3 días