import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Rutas base
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configuración general
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", (
    "Eres un asistente útil en español. Responde de forma breve, clara y amable."
)).strip()

# Configuración del chat
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "300"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))

# Control de acceso
AUTHORIZED_USER_IDS = os.getenv("AUTHORIZED_USER_IDS", "").strip()
AUTHORIZED_USERS = set(int(uid) for uid in AUTHORIZED_USER_IDS.split(",") if uid.strip()) if AUTHORIZED_USER_IDS else set()

def ensure_config():
    """Verifica que la configuración mínima esté completa."""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if missing:
        raise RuntimeError(
            "Faltan variables de entorno: " + ", ".join(missing)
        )
    print("✅ Configuración validada")
    print(f"📁 Directorio base: {BASE_DIR}")
    print(f"📝 Directorio de logs: {LOGS_DIR}")
    print(f"🤖 Modelo: {OPENAI_MODEL}")
    print(f"🔒 Usuarios autorizados: {'Todos' if not AUTHORIZED_USERS else len(AUTHORIZED_USERS)}")

def is_user_authorized(user_id: int) -> bool:
    """Verifica si un usuario está autorizado a usar el bot."""
    if not AUTHORIZED_USERS:  # Si no hay restricciones, todos pueden usar
        return True
    return user_id in AUTHORIZED_USERS
