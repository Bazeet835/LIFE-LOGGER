import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

GITHUB_BRANCH = "main"
BUFFER_FILE = "buffer.txt"


# 🔥 Safety Check — prevents silent crashes later
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is missing!")

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is missing!")

if not GITHUB_REPO:
    raise ValueError("GITHUB_REPO is missing!")