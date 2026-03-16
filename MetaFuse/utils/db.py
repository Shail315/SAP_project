import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "metafuse.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id                         INTEGER PRIMARY KEY AUTOINCREMENT,
            name                       TEXT    NOT NULL,
            email                      TEXT    NOT NULL UNIQUE,
            password_hash              TEXT    NOT NULL,
            created_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_sessions (
            id                         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                    INTEGER NOT NULL,
            token_hash                 TEXT    NOT NULL UNIQUE,
            expires_at                 TIMESTAMP NOT NULL,
            created_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS videos (
            id                         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                    INTEGER,
            filename                   TEXT    NOT NULL,
            local_path                 TEXT,
            cloudinary_video_url       TEXT,
            cloudinary_video_public_id TEXT,
            transcript                 TEXT,
            created_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS audio_chunks (
            id                          INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id                    INTEGER NOT NULL,
            chunk_filename              TEXT,
            cloudinary_audio_url        TEXT,
            cloudinary_audio_public_id  TEXT,
            created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );

        CREATE TABLE IF NOT EXISTS metadata (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id             INTEGER NOT NULL UNIQUE,
            title                TEXT,
            description          TEXT,
            caption              TEXT,
            hashtags             TEXT,
            tags                 TEXT,
            keywords             TEXT,
            summary              TEXT,
            thumbnail_ideas      TEXT,
            chapters             TEXT,
            thumbnail_url        TEXT,
            thumbnail_local_path TEXT,
            created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );
    """)

    # Ensure backwards compatibility for databases created before new columns.
    video_cols = {
        r["name"] for r in conn.execute("PRAGMA table_info(videos)").fetchall()
    }
    if "user_id" not in video_cols:
        conn.execute("ALTER TABLE videos ADD COLUMN user_id INTEGER")

    metadata_cols = {
        r["name"] for r in conn.execute("PRAGMA table_info(metadata)").fetchall()
    }
    for col in ("keywords", "summary", "thumbnail_ideas"):
        if col not in metadata_cols:
            conn.execute(f"ALTER TABLE metadata ADD COLUMN {col} TEXT")

    conn.commit()
    conn.close()


def save_video(filename, local_path=None, cloudinary_video_url=None,
               cloudinary_video_public_id=None, user_id=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO videos
           (user_id, filename, local_path, cloudinary_video_url, cloudinary_video_public_id)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, filename, local_path, cloudinary_video_url, cloudinary_video_public_id),
    )
    video_id = c.lastrowid
    conn.commit()
    conn.close()
    return video_id


def save_transcript(video_id, transcript):
    conn = get_connection()
    conn.execute(
        "UPDATE videos SET transcript = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (transcript, video_id),
    )
    conn.commit()
    conn.close()


def save_audio_chunk(video_id, chunk_filename, cloudinary_url=None, cloudinary_public_id=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO audio_chunks (video_id, chunk_filename, cloudinary_audio_url, cloudinary_audio_public_id) VALUES (?, ?, ?, ?)",
        (video_id, chunk_filename, cloudinary_url, cloudinary_public_id),
    )
    conn.commit()
    conn.close()


def get_transcript(video_id):
    conn = get_connection()
    row = conn.execute("SELECT transcript FROM videos WHERE id = ?", (video_id,)).fetchone()
    conn.close()
    return row["transcript"] if row else None


def get_video(video_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def upsert_metadata(video_id, **kwargs):
    """Insert or update individual metadata fields for a video."""
    if not kwargs:
        return
    conn = get_connection()
    c = conn.cursor()
    row = c.execute("SELECT id FROM metadata WHERE video_id = ?", (video_id,)).fetchone()
    if row:
        set_clause = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [video_id]
        c.execute(
            f"UPDATE metadata SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE video_id = ?",
            values,
        )
    else:
        kwargs["video_id"] = video_id
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join("?" * len(kwargs))
        c.execute(
            f"INSERT INTO metadata ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
    conn.commit()
    conn.close()


def get_metadata(video_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM metadata WHERE video_id = ?", (video_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_all_videos():
    """Return all videos with their titles and thumbnail URLs for future web UI."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT v.id, v.filename, v.cloudinary_video_url, v.created_at,
               m.title, m.thumbnail_url
        FROM videos v
        LEFT JOIN metadata m ON m.video_id = v.id
        ORDER BY v.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_user(name, email, password_hash):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email.lower().strip(), password_hash),
    )
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user_by_email(email):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email.lower().strip(),),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_session(user_id, token_hash, expires_at):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO user_sessions (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, token_hash, expires_at),
    )
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id


def get_session_by_hash(token_hash):
    conn = get_connection()
    row = conn.execute(
        """SELECT s.*, u.name, u.email
           FROM user_sessions s
           JOIN users u ON u.id = s.user_id
           WHERE s.token_hash = ?""",
        (token_hash,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session_by_hash(token_hash):
    conn = get_connection()
    conn.execute("DELETE FROM user_sessions WHERE token_hash = ?", (token_hash,))
    conn.commit()
    conn.close()


def purge_expired_sessions():
    conn = get_connection()
    conn.execute("DELETE FROM user_sessions WHERE expires_at <= CURRENT_TIMESTAMP")
    conn.commit()
    conn.close()


def get_user_videos(user_id):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT v.id, v.filename, v.local_path, v.cloudinary_video_url, v.created_at,
               m.title, m.description, m.tags, m.keywords, m.summary, m.thumbnail_url
        FROM videos v
        LEFT JOIN metadata m ON m.video_id = v.id
        WHERE v.user_id = ?
        ORDER BY v.created_at DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_video_for_user(video_id, user_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM videos WHERE id = ? AND user_id = ?",
        (video_id, user_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_video_with_metadata_for_user(video_id, user_id):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT v.*, m.title, m.description, m.caption, m.hashtags, m.tags,
               m.keywords, m.summary, m.thumbnail_ideas, m.chapters,
               m.thumbnail_url, m.thumbnail_local_path
        FROM videos v
        LEFT JOIN metadata m ON m.video_id = v.id
        WHERE v.id = ? AND v.user_id = ?
        """,
        (video_id, user_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
