from fastapi import APIRouter, Depends, HTTPException
from datetime import timedelta, datetime, UTC
from typing import Annotated
from sqlalchemy import select
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, defer
from authlib.integrations.starlette_client import OAuth
import os
from jose import jwt, JWTError
from app.config import settings
from app.schemas import GoogleUser
from app.models import User
from app.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.config import Config

ALGORITHM = settings.ALGORITHM #It ensures secure token creation and validation for authentication and authorization.
#  Using the bcrypt algorithm for securely storing user passwords.
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# tells FastAPI to expect a bearer token (like JWT) in the Authorization header for protected routes.
oauth_bearer = OAuth2PasswordBearer(tokenUrl="auth/token",scheme_name="JWT")

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID or None
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET or None

if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_SECRET is None:
    raise Exception('Missing env variables')



# oauth = OAuth()

config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid email profile",
        "prompt": "select_account"
    }
)
async def authenticate_user(username: str, password: str, db: AsyncSession = Depends(get_session)):
    user = (await db.execute(select(User).filter(User.username == username))).scalars().first()

    if not user:
        return False

    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}

    expires = datetime.now(UTC) + expires_delta

    encode.update({"exp": expires})

    return jwt.encode(encode,settings.SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(username: str, user_id: int, expires_delta: timedelta):
    return create_access_token(username, user_id, expires_delta)


def decode_token(token):
    return jwt.decode(token,settings.SECRET_KEY, algorithms=[ALGORITHM])

async def get_current_user(token: Annotated[str, Depends(oauth_bearer)],db: AsyncSession = Depends(get_session)):
    try:
        payload = jwt.decode(token,settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")

        user = (
            await db.execute(
                select(User)
                .options(defer(User.hashed_password), defer(User.google_sub))
                .filter(User.username == username)
            )
        ).scalars().first()
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
#def token_expired(token: str):  # Remove Depends annotation

async def token_expired(token: str):
    try:
        payload = decode_token(token)
        if not datetime.fromtimestamp(payload.get('exp'), UTC) > datetime.now(UTC):
            return True
        return False
    except JWTError:
        return True  # Consider invalid tokens as expired

# google sub is a unique identifier for a user in Google authentication.
async def get_user_by_google_sub(google_sub: str, db: AsyncSession = Depends(get_session)):
    google_sub_str = str(google_sub)
    stmt = select(User).filter(User.google_sub == google_sub_str)
    result = await db.execute(stmt)
    return result.scalars().first()
# This function creates or updates a user in the database using Google account info
async def create_user_from_google_info(google_user: GoogleUser, db: AsyncSession = Depends(get_session)):
    google_sub = google_user.sub
    email = google_user.email
    existing_user = (await db.execute(select(User).filter(User.email == email))).scalars().first()
    if existing_user:

        #existing_user.google_sub = str(google_sub)
        existing_user.google_sub = str(google_sub)
        await db.commit()
        return existing_user
    else:

        new_user = User(
            username=email,
            email=email,
            google_sub=str(google_sub),

        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
#This line sets up a reusable dependency for FastAPI routes. It means
# that when you use user_dependency in a route, FastAPI will automatically
# run the get_current_user function and give you the current logged-in user.
#user_dependency = Annotated[dict, Depends(get_current_user)]
user_dependency = Annotated[User, Depends(get_current_user)]