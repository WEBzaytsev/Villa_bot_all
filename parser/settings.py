import json
from os import environ

REQUIRED_ENV = ['POSTGRES_DB', 'POSTGRES_USER',
                'POSTGRES_PASSWORD', 'DB_ADDRESS', 'DB_PORT',
                'OWNER_TOKEN', 'STORAGE_IDS', 'PROXY', 'SLEEP_INTERVAL']
for var in REQUIRED_ENV:
    if var not in environ:
        raise EnvironmentError(f"{var} is not set.")

POSTGRES_DB = environ.get('POSTGRES_DB')
POSTGRES_USER = environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = environ.get('POSTGRES_PASSWORD')
DB_ADDRESS = environ.get('DB_ADDRESS')
DB_PORT = environ.get('DB_PORT')
OWNER_TOKEN = environ.get('OWNER_TOKEN')
STORAGE_IDS = json.loads(environ['STORAGE_IDS'])
PROXY = json.loads(environ['PROXY'])
SLEEP_INTERVAL = int(environ.get('SLEEP_INTERVAL'))
