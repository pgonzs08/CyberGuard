import os
import sys

MONGO_URI = os.environ["MONGO_URI"]
DEBUG = os.environ.get("DEBUG", "").strip().lower() in {"1", "true", "on", "yes"}
EXPIRATION_MINUTES = 3*60*24 #3 días