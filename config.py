import os
from dotenv import load_dotenv

# .env dosyasının içindeki gizli bilgileri okur
load_dotenv()

# Groq Şifresi
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.1-8b-instant"

# Telegram Şifreleri (ID değerini Telethon için sayıya çeviriyoruz)
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")

# Takip edilecek sitenin ana adresi
BASE_URL = "https://dilayats.github.io/alisveris-test-sitesi/"