# MetaFuse FastAPI Backend

FastAPI backend that mirrors the Gradio pipeline while adding users and user-scoped history.

## Run

```bash
cd MetaFuse
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

## Main endpoints

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/videos/upload`
- `POST /api/videos/{video_id}/generate`
- `GET /api/videos/history`
- `GET /api/videos/{video_id}`
- `GET /api/videos/{video_id}/file`

## Notes

- Existing SQLite DB is migrated in-place during `init_db()`.
- Videos are linked to `users.id` through `videos.user_id`.
- Metadata generation reuses existing pipelines for titles, description, tags, hashtags, chapters, and thumbnail generation.
