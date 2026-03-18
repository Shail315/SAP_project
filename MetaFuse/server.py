from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import os

import gradio as gr
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from pydantic import BaseModel, EmailStr

from app import app as gradio_blocks
from utils.db import create_user, get_user_by_email, get_user_by_id, init_db


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
FRONTEND_DEV_URL = "https://fictional-system-97j7p77jq47xf6rp-5173.app.github.dev/"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

api = FastAPI(title="MetaFuse API", version="1.0.0")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["https://fictional-system-97j7p77jq47xf6rp-5173.app.github.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = get_user_by_id(int(user_id))
    if not user:
        raise credentials_exception
    return user


def _frontend_index() -> Path:
    return Path(__file__).resolve().parent.parent / "frontend" / "dist" / "index.html"


def _serve_frontend_or_redirect(path: str):
    index_file = _frontend_index()
    if index_file.exists():
        return FileResponse(index_file)
    return RedirectResponse(url=f"{FRONTEND_DEV_URL}{path}")


@api.on_event("startup")
def on_startup() -> None:
    init_db()
    dist_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    assets_dir = dist_dir / "assets"
    if assets_dir.exists() and not any(route.path == "/assets" for route in api.routes):
        api.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@api.get("/")
def root_redirect():
    return RedirectResponse(url="/app")


@api.get("/app")
def landing_page():
    return _serve_frontend_or_redirect("/app")


@api.get("/login")
def login_page():
    return _serve_frontend_or_redirect("/login")


@api.get("/signup")
def signup_page():
    return _serve_frontend_or_redirect("/signup")

@api.get("/gradio")
def gradio_page():
    return RedirectResponse(url="https://fictional-system-97j7p77jq47xf6rp-8002.app.github.dev/")


@api.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest):
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    try:
        user_id = create_user(
            name=payload.name.strip(),
            email=payload.email,
            password_hash=hash_password(payload.password),
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Email is already registered") from exc

    return UserResponse(id=user_id, name=payload.name.strip(), email=payload.email)


@api.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    try:
        is_valid = verify_password(payload.password, user["password_hash"])
    except (UnknownHashError, ValueError):
        # Legacy or malformed hashes should not crash auth; return a normal auth failure.
        is_valid = False

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        subject=str(user["id"]),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(access_token=access_token)


@api.get("/auth/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
    )


# api = gr.mount_gradio_app(api, gradio_blocks, path="/gradio")
