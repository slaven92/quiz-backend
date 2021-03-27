from bson import ObjectId

from . import schemas, database
from .security import verify_password, get_password_hash
from typing import List

#adds field id to the dictionary
def convert_data(data):
    data["id"] = str(data["_id"])
    return data

async def get_user(user_id: str):
    user = await database.mongoUsers.find_one({"_id":ObjectId(user_id)})
    if user is None:
        return None
    return schemas.User(**convert_data(user))


async def get_user_by_email(email: str):
    user = await database.mongoUsers.find_one({"email":email})
    if user is None:
        return None
    return schemas.UserInDB(**convert_data(user))


async def get_users(skip: int = 0, limit: int = 100):
    resp: List = []
    async for user in database.mongoUsers.find().skip(skip).limit(limit):
        tmpUser = schemas.User(**convert_data(user))
        resp.append(tmpUser)
    return resp


async def create_user(user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = schemas.UserInDB(
        email=user.email, hashed_password=hashed_password, full_name=user.full_name
    )
    user_id = await database.mongoUsers.insert_one(db_user.dict())
    db_user.id = str(user_id.inserted_id)

    return db_user


async def get_items(skip: int = 0, limit: int = 100):
    resp: List = []
    async for item in database.mongoItems.find().skip(skip).limit(limit):
        tmpItem = schemas.Item(**convert_data(item))
        resp.append(tmpItem)
    return resp


async def create_user_item(item: schemas.ItemCreate, user_id: str):
    db_item = schemas.Item(**item.dict(), owner_id=user_id)
    
    item_id = await database.mongoItems.insert_one(db_item.dict())
    db_item.id = str(item_id.inserted_id)
    
    return db_item


async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user