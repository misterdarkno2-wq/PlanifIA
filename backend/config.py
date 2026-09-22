import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')
DB = dict(host=os.getenv('DB_HOST', '127.0.0.1'), port=int(os.getenv('DB_PORT', '3306')),
          user=os.getenv('DB_USER', 'planifia_app'), password=os.getenv('DB_PASSWORD', ''),
          database=os.getenv('DB_NAME', 'planifia'))
DB_IPV4 = os.getenv('DB_IPV4', 'false').lower() == 'true'
ORIGIN = os.getenv('APP_ORIGIN', 'http://127.0.0.1:8000').rstrip('/')
COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
TIMEZONE = ZoneInfo(os.getenv('APP_TIMEZONE', 'America/Santiago'))

def local_now():
    return datetime.now(TIMEZONE).replace(tzinfo=None)
