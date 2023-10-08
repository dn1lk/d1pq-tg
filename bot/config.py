import os

DEBUG = int(os.getenv('DEBUG', 0))
LOG_TO_FILE = int(os.getenv('LOG_TO_FILE', 0))

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID'))
BOT_SKIP_UPDATES = int(os.getenv('BOT_SKIP_UPDATES', 0))

WEBHOOK_USE = int(os.getenv('WEBHOOK_USE', 0))
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
WEBHOOK_HOST = os.getenv('HOST')
WEBHOOK_PORT = os.getenv('PORT')
WEBHOOK_URL = os.getenv('WEBHOOK_URL') or f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}"
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH') or f"webhook/bot{BOT_TOKEN}"

YC_SERVICE_ACCOUNT_FILE_CREDENTIALS = os.getenv('YC_SERVICE_ACCOUNT_FILE_CREDENTIALS')
YDB_ENDPOINT = os.getenv('YDB_ENDPOINT')
YDB_DATABASE = os.getenv('YDB_DATABASE')

REDIS_USE = int(os.getenv('REDIS_USE', 0))
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_USER = os.getenv('REDIS_USER')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_DB = os.getenv('REDIS_DB')
REDIS_URL = os.getenv('REDIS_URL') or f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
