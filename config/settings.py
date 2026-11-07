import os
from dotenv import load_dotenv

# Находим корневую папку проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Загружаем .env
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Получаем API Key
FACEIT_API_KEY = os.getenv("FACEIT_API_KEY")