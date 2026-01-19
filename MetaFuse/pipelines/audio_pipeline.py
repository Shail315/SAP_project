import hashlib
from pathlib import Path

CACHE_DIR = Path("data/transcripts")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def cache_key(video_path):
    return hashlib.md5(video_path.read_bytes()).hexdigest()

def load_cache(key):
    f = CACHE_DIR / f"{key}.txt"
    return f.read_text() if f.exists() else None

def save_cache(key, text):
    f = CACHE_DIR / f"{key}.txt"
    f.write_text(text)
