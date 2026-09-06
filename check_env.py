from pathlib import Path
from dotenv import load_dotenv
import os

ENV_PATH = Path(__file__).resolve().parent / ".env"
print("Looking for .env at:", ENV_PATH)
print("Exists:", ENV_PATH.exists())

load_dotenv(dotenv_path=ENV_PATH)

print("AWS_ACCESS_KEY_ID:", repr(os.getenv("AWS_ACCESS_KEY_ID")))
print("AWS_SECRET_ACCESS_KEY set:", os.getenv("AWS_SECRET_ACCESS_KEY") is not None)
print("AWS_REGION:", repr(os.getenv("AWS_REGION")))