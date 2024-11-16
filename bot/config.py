import os

DEBUG = int(os.getenv("DEBUG", "0"))
LOG_TO_FILE = int(os.getenv("LOG_TO_FILE", "0"))

LOCALE_PATH = "core/locales"
LOG_PATH = "logs"

BOT_TOKEN = os.environ["BOT_TOKEN"]
BOT_OWNER_ID = int(os.environ["BOT_OWNER_ID"])
BOT_SKIP_UPDATES = bool(int(os.getenv("BOT_SKIP_UPDATES", "0")))

WEBHOOK_USE = int(os.getenv("WEBHOOK_USE", "0"))
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
WEBHOOK_HOST = os.getenv("HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("PORT", "8000"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", f"webhook/bot{BOT_TOKEN}")

YC_CATALOG_ID = os.environ["YC_CATALOG_ID"]
YC_SERVICE_ACCOUNT_FILE_CREDENTIALS = os.environ["YC_SERVICE_ACCOUNT_FILE_CREDENTIALS"]
YDB_ENDPOINT = os.environ["YDB_ENDPOINT"]
YDB_DATABASE = os.environ["YDB_DATABASE"]

REDIS_USE = int(os.getenv("REDIS_USE", "0"))
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
REDIS_DB = os.environ["REDIS_DB"]
REDIS_URL = os.getenv("REDIS_URL", f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
