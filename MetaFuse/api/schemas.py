from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthResponse(BaseModel):
    token: str
    user: dict


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


class UploadResponse(BaseModel):
    video_id: int
    status: str
    transcript: str
    raw_tags: list[str]
    timed_segments: list[dict]
    video_url: Optional[str] = None


class GenerateRequest(BaseModel):
    regenerate_tags: bool = True


class MetadataResponse(BaseModel):
    title: str
    description: str
    tags: str
    keywords: str
    summary: str
    thumbnail_ideas: str
    caption: str
    hashtags: str
    chapters: str
    thumbnail_url: Optional[str] = None


class HistoryItem(BaseModel):
    id: int
    filename: str
    created_at: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
