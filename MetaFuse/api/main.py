import os
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from utils.config_loader import load_config
from utils.db import (
    create_session,
    create_user,
    delete_session_by_hash,
    get_session_by_hash,
    get_transcript,
    get_user_by_email,
    get_user_by_id,
    get_user_videos,
    get_video_for_user,
    get_video_with_metadata_for_user,
    init_db,
    purge_expired_sessions,
    save_audio_chunk,
    save_transcript,
    save_video,
    upsert_metadata,
)
from pipelines.audio_pipeline import split_audio
from pipelines.cloudinary_pipeline import upload_audio as cld_upload_audio
from pipelines.cloudinary_pipeline import upload_video as cld_upload_video
from pipelines.description_pipeline import generate_description
from pipelines.caption_pipeline import generate_caption
from pipelines.hashtags_pipeline import generate_hashtags
from pipelines.keyword_pipeline import extract_keywords
from pipelines.llm_pipeline import generate_chapters, refine_tags_with_llm
from pipelines.thumbnail_pipeline import generate_thumbnail
from pipelines.title_pipeline import generate_title
from pipelines.transcript_pipeline import transcribe

from .schemas import GenerateRequest, LoginRequest, SignupRequest
from .security import (
    hash_password,
    hash_token,
    make_session_token,
    session_expiry_timestamp,
    verify_password,
)


cfg = load_config()
app = FastAPI(title="MetaFuse API", version="1.0.0")
auth_scheme = HTTPBearer(auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SUMMARY_PROMPT = ChatPromptTemplate.from_template(
    """You are a YouTube content strategist.

Transcript:
{transcript}

Create:
1) A concise 3-5 sentence video summary.
2) 3 distinct thumbnail ideas in numbered lines.

Return exactly in this format:
Summary: <summary text>
Thumbnail Ideas:
1. ...
2. ...
3. ...
"""
)


def _llm_client():
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return ChatOpenAI(
        model=cfg["llm"]["model"],
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=cfg["llm"].get("temperature", 0.3),
        max_tokens=cfg["llm"].get("max_tokens", 1024),
    )


def _summary_and_ideas(transcript: str) -> tuple[str, str]:
    llm = _llm_client()
    if not llm:
        return "N/A (API key not set)", "N/A (API key not set)"

    try:
        msg = SUMMARY_PROMPT.format_messages(transcript=transcript[:3500])
        raw = llm.invoke(msg).content.strip()
        summary = raw
        ideas = ""

        if "Thumbnail Ideas:" in raw:
            before, after = raw.split("Thumbnail Ideas:", 1)
            summary = before.replace("Summary:", "").strip()
            ideas = after.strip()
        return summary or "N/A", ideas or "N/A"
    except Exception as exc:
        return f"Error: {exc}", f"Error: {exc}"


def _serialize_user(user_row: dict) -> dict:
    return {
        "id": user_row["id"],
        "name": user_row["name"],
        "email": user_row["email"],
    }


def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required")

    purge_expired_sessions()
    token_hash = hash_token(credentials.credentials)
    session = get_session_by_hash(token_hash)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = get_user_by_id(session["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/api/health")
def health_check():
    return {"ok": True}


@app.post("/api/auth/signup")
def signup(payload: SignupRequest):
    existing = get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = create_user(
        name=payload.name.strip(),
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    user = get_user_by_id(user_id)
    token = make_session_token()
    create_session(user_id, hash_token(token), session_expiry_timestamp())

    return {"token": token, "user": _serialize_user(user)}


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = make_session_token()
    create_session(user["id"], hash_token(token), session_expiry_timestamp())
    return {"token": token, "user": _serialize_user(user)}


@app.post("/api/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    if not credentials:
        return {"ok": True}
    delete_session_by_hash(hash_token(credentials.credentials))
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: dict = Depends(_get_current_user)):
    return _serialize_user(user)


@app.post("/api/videos/upload")
def upload_video(
    file: UploadFile = File(...),
    user: dict = Depends(_get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    videos_dir = Path(cfg["paths"]["videos"])
    videos_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename).name
    local_path = videos_dir / safe_name
    suffix = 1
    while local_path.exists():
        local_path = videos_dir / f"{Path(safe_name).stem}_{suffix}{Path(safe_name).suffix}"
        suffix += 1

    with open(local_path, "wb") as out:
        out.write(file.file.read())

    video_url, video_pid = cld_upload_video(local_path)
    video_id = save_video(
        filename=local_path.name,
        local_path=str(local_path),
        cloudinary_video_url=video_url,
        cloudinary_video_public_id=video_pid,
        user_id=user["id"],
    )

    try:
        chunks = split_audio(local_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audio split failed: {exc}")

    for chunk in chunks:
        audio_url, audio_pid = cld_upload_audio(chunk)
        save_audio_chunk(video_id, chunk.name, audio_url, audio_pid)

    transcript, timed_segments = transcribe(chunks)
    if not transcript.strip():
        raise HTTPException(status_code=500, detail="Transcription failed")

    save_transcript(video_id, transcript)
    raw_tags = extract_keywords(transcript, top_n=50)
    upsert_metadata(video_id, keywords=", ".join(raw_tags))

    return {
        "video_id": video_id,
        "status": "processed",
        "transcript": transcript,
        "raw_tags": raw_tags,
        "timed_segments": timed_segments,
        "video_url": video_url,
    }


@app.post("/api/videos/{video_id}/generate")
def generate_metadata(
    video_id: int,
    payload: GenerateRequest,
    user: dict = Depends(_get_current_user),
):
    video = get_video_for_user(video_id, user["id"])
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    transcript = get_transcript(video_id)
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript not found")

    raw_keywords = extract_keywords(transcript, top_n=50)
    max_tags = cfg.get("tags", {}).get("max_tags", 10)

    if payload.regenerate_tags:
        tags_list = refine_tags_with_llm(transcript, raw_keywords, max_tags=max_tags)
    else:
        tags_list = raw_keywords[:max_tags]

    tags = ", ".join(tags_list)
    title = generate_title(transcript, tags_list)
    description = generate_description(transcript, tags_list)
    caption = generate_caption(transcript, tags_list)
    hashtags = generate_hashtags(transcript, tags_list)
    chapters = generate_chapters(transcript=transcript)
    summary, thumbnail_ideas = _summary_and_ideas(transcript)

    thumb_img, thumb_url, thumb_prompt = generate_thumbnail(
        video_id=video_id,
        transcript=transcript,
        title=title,
        tags=tags_list,
    )

    upsert_metadata(
        video_id,
        title=title,
        description=description,
        caption=caption,
        hashtags=hashtags,
        tags=tags,
        keywords=", ".join(raw_keywords),
        summary=summary,
        thumbnail_ideas=thumbnail_ideas if thumbnail_ideas != "N/A" else thumb_prompt,
        chapters=chapters,
        thumbnail_url=thumb_url or "",
        thumbnail_local_path=thumb_img or "",
    )

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "keywords": ", ".join(raw_keywords),
        "summary": summary,
        "thumbnail_ideas": thumbnail_ideas if thumbnail_ideas != "N/A" else thumb_prompt,
        "caption": caption,
        "hashtags": hashtags,
        "chapters": chapters,
        "thumbnail_url": thumb_url,
    }


@app.get("/api/videos/history")
def history(user: dict = Depends(_get_current_user)):
    return get_user_videos(user["id"])


@app.get("/api/videos/{video_id}")
def video_detail(video_id: int, user: dict = Depends(_get_current_user)):
    row = get_video_with_metadata_for_user(video_id, user["id"])
    if not row:
        raise HTTPException(status_code=404, detail="Video not found")

    if row.get("cloudinary_video_url"):
        row["playback_url"] = row["cloudinary_video_url"]
    else:
        row["playback_url"] = f"/api/videos/{video_id}/file"
    return row


@app.get("/api/videos/{video_id}/file")
def serve_video_file(video_id: int, user: dict = Depends(_get_current_user)):
    video = get_video_for_user(video_id, user["id"])
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    local_path = video.get("local_path")
    if not local_path or not Path(local_path).exists():
        raise HTTPException(status_code=404, detail="Local file missing")

    return FileResponse(local_path, media_type="video/mp4", filename=video["filename"])
