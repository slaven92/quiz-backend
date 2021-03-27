from datetime import timedelta
from typing import List

from fastapi import Depends, FastAPI, HTTPException, WebSocket, status
from fastapi.security import OAuth2PasswordRequestForm
from starlette.concurrency import run_until_first_complete

from . import crud, schemas
from .deps import get_current_active_user
from .security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from .websock import broadcast, chatroom_ws_receiver, chatroom_ws_sender, html

from fastapi.responses import HTMLResponse
app = FastAPI(on_startup=[broadcast.connect], on_shutdown=[broadcast.disconnect])


@app.post("/users/", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate,
    current_user = Depends(get_current_active_user),
):
    db_user = await crud.get_user_by_email(email=str(user.email))

    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    return await crud.create_user(user=user)


@app.get("/users/", response_model=List[schemas.User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_active_user),
):
    users = await crud.get_users(skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
async def read_user(
    user_id: str,
    current_user = Depends(get_current_active_user),
):
    db_user = await crud.get_user(user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
async def create_item_for_user(
    user_id: str,
    item: schemas.ItemCreate,
    current_user = Depends(get_current_active_user),
):
    return await crud.create_user_item(item=item, user_id=user_id)


@app.get("/items/", response_model=List[schemas.Item])
async def read_items(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_active_user),
):
    items = await crud.get_items(skip=skip, limit=limit)
    return items


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await crud.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    await websocket.accept()
    await run_until_first_complete(
        (chatroom_ws_receiver, {"websocket": websocket, "channel": channel}),
        (chatroom_ws_sender, {"websocket": websocket, "channel": channel}),
    )
