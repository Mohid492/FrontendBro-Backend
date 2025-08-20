from authlib.integrations.base_client import OAuthError
from authlib.oauth2.rfc6749 import OAuth2Token
from fastapi import APIRouter, Depends, HTTPException
from datetime import timedelta
from typing import Annotated
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm
from app.models import User
from app.schemas import CreateUserRequest, GoogleUser, Token, RefreshTokenRequest
from .services import create_access_token, authenticate_user, bcrypt_context, create_refresh_token, \
    create_user_from_google_info, get_user_by_google_sub, token_expired, decode_token, user_dependency
from app.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from .services import oauth
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select

import logging
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
# In app/routers/auth/auth.py
GOOGLE_REDIRECT_URI = "http://127.0.0.1:8000/auth/callback/google"
FRONTEND_URL = settings.FRONTEND_URL

# @router.get("/google")
# async def login_google(request: Request):
#     return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)
@router.get("/google", include_in_schema=False)
async def login_google(request: Request):
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)

#This below function handles the Google OAuth callback. It:
# Receives the OAuth response from Google.
# Extracts user info from the response.
# Checks if the user already exists in the database.
# If not, creates a new user with the Google info.
# Generates access and refresh tokens for the user.
# Redirects the user to the frontend, passing the tokens as URL parameters.
@router.get("/callback/google")
async def auth_google(request: Request, db: AsyncSession = Depends(get_session)):
    try:
        user_response: OAuth2Token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    user_info = user_response.get("userinfo")

    logger.info(f"User info received: {user_info}")

    google_user = GoogleUser(**user_info)

    existing_user = await get_user_by_google_sub(google_user.sub, db)

    if existing_user:
        logger.info(f"Existing user found: {existing_user.username}")
        user = existing_user
    else:
        logger.info(f"Creating new user with Google info: {google_user}")
        user = await create_user_from_google_info(google_user, db)

    access_token = create_access_token(user.username, user.id, timedelta(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(user.username, user.id, timedelta(settings.REFRESH_TOKEN_EXPIRE_TIME))

    return RedirectResponse(f"{FRONTEND_URL}/auth?access_token={access_token}&refresh_token={refresh_token}")

@router.post("/create-user", status_code=status.HTTP_201_CREATED)
async def create_user(create_user_request: CreateUserRequest, db: AsyncSession = Depends(get_session)):
    # Check if user already exists by username or email
    existing_user = (await db.execute(
        select(User).filter(
            (User.username == create_user_request.username) |
            (User.email == create_user_request.username)
        )
    )).scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username/email already exists"
        )

    create_user_model = User(
        username=create_user_request.username,
        email=create_user_request.username,
        hashed_password=bcrypt_context.hash(create_user_request.password)
    )

    db.add(create_user_model)
    await db.commit()
    await db.refresh(create_user_model)

    return {"username": create_user_model.username, "email": create_user_model.email, "id": create_user_model.id}


@router.get("/get-user", status_code=status.HTTP_201_CREATED)
async def get_user(user: user_dependency,db: AsyncSession = Depends(get_session)):
    return user

@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],db: AsyncSession = Depends(get_session)):
    user = await authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")

    access_token = create_access_token(user.username, user.id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(user.username, user.id, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_TIME))

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token_request: RefreshTokenRequest,db: AsyncSession = Depends(get_session)):
    token = refresh_token_request.refresh_token

    if await  token_expired(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is expired.")

    user = decode_token(token)

    access_token = create_access_token(user["sub"], user["id"], timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(user["sub"], user["id"], timedelta(days=settings.REFRESH_TOKEN_EXPIRE_TIME))

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get("/verify-token")
async def verify_token(current_user: user_dependency):
    """Endpoint to verify if token is valid - useful for testing in docs"""
    return {"user": current_user.username, "user_id": current_user.id}