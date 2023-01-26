import logging
from os import environ

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

REQUIRED_ENV = ['RENTEE_TOKEN', 'OWNER_TOKEN', 'MONGO_HOST',
                'MONGO_PORT', 'MONGO_PASSWORD', 'MONGO_USERNAME']

for var in REQUIRED_ENV:
    if var not in environ:
        raise EnvironmentError(f"{var} is not set.")

BOT_TOKEN = environ.get('OWNER_TOKEN')
MONGO_HOST = environ.get('MONGO_HOST')
MONGO_PORT = environ.get('MONGO_PORT')
MONGO_PASSWORD = environ.get('MONGO_PASSWORD')
MONGO_USERNAME = environ.get('MONGO_USERNAME')

bot = Bot(token=BOT_TOKEN)

storage = MongoStorage(host=MONGO_HOST,
                       port=MONGO_PORT,
                       db_name='renter',
                       username=MONGO_USERNAME,
                       password=MONGO_PASSWORD,)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=logging.INFO)
