import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

import db
from cruds.main import get_user_by_username
from shcemas.main import TokenData, UserInDB


SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Require an explicit secret in deployed (serverless) environments; allow a
    # local dev fallback so running the app locally does not need extra setup.
    if os.environ.get("VERCEL"):
        raise RuntimeError("SECRET_KEY is not set")
    SECRET_KEY = "dev-insecure-secret-key-change-me"

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "access_token")
COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "lax")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)

async def get_user(db_session: AsyncSession, username: str) -> UserInDB | None:
    db_user = await get_user_by_username(db_session, username)
    if db_user is None:
        return None
    return UserInDB(
        id=db_user.id,
        username=db_user.username,
        hashed_password=db_user.password_hash,
    )

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(
    db_session: AsyncSession,
    username: str,
    password: str,
) -> UserInDB | None:
    user = await get_user(db_session, username)
    if user is None:
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db_session: AsyncSession = Depends(db.get_dbsession),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    raw_token = token or request.cookies.get(COOKIE_NAME)
    if not raw_token:
        raise credentials_exception

    try:
        payload = jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except PyJWTError:
        raise credentials_exception
    user = await get_user(db_session, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user.id


async def get_current_user_optional(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db_session: AsyncSession = Depends(db.get_dbsession),
) -> int | None:
    try:
        return await get_current_user(request, token, db_session)
    except HTTPException:
        return None