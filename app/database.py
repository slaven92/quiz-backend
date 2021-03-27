import os
import motor.motor_asyncio

MONGO_DATABASE_URL = os.environ["MONGO_DATABASE_URL"]

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DATABASE_URL)
db=client.fastapi

mongoUsers = db['users']
mongoItems = db['items']