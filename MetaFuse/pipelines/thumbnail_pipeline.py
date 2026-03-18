"""Thumbnail pipeline — generates a YouTube-style thumbnail via OpenRouter
using Gemini models and stores it in Cloudinary, keyed by video_id.

Flow:
  1. Fetch transcript from DB (or accept it directly).
  2. Build a vivid image-generation prompt via Gemini text model.
  3. Generate the thumbnail image via Gemini image-generation model.
  4. Save the image locally to a temp file.
  5. Upload to Cloudinary under metafuse/thumbnails/video_{video_id}.
  6. Return (local_path, cloudinary_url, prompt_used).
"""

import os
import re
import tempfile
from urllib.parse import quote_plus
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

from utils.db import get_transcript
from pipelines.cloudinary_pipeline import upload_image

load_dotenv()

# ── OpenRouter + Gemini models ─────────────────────────────────────────────
_OPENROUTER_BASE = "https://openrouter.ai/api/v1"
_TEXT_MODEL = "google/gemini-2.5-flash"
_IMAGE_MODEL = "google/gemini-2.5-flash-image-preview"

# ── Max characters of transcript fed to Gemini (keep cost low) ─────────────
_TRANSCRIPT_CHARS = 3000


def _download_image_from_url(url: str) -> bytes:
    scheme = urlparse(url).scheme
    if scheme not in ("http", "https"):
        raise RuntimeError("Invalid image URL returned by model")
    img_resp = requests.get(url, timeout=120)
    img_resp.raise_for_status()
    return img_resp.content


def _decode_data_url(data_url: str) -> bytes:
    import base64

    if not data_url.startswith("data:image") or "," not in data_url:
        raise RuntimeError("Invalid data URL returned by model")
    _, b64_data = data_url.split(",", 1)
    return base64.b64decode(b64_data)


def _extract_image_bytes_from_response(data: dict) -> bytes:
    import base64

    # OpenAI-style image response
    if data.get("data") and isinstance(data["data"], list):
        first = data["data"][0] or {}
        if first.get("b64_json"):
            return base64.b64decode(first["b64_json"])
        if first.get("url"):
            return _download_image_from_url(first["url"])

    # Chat-completions style response from some providers
    choices = data.get("choices")
    if choices and isinstance(choices, list):
        message = (choices[0] or {}).get("message") or {}

        # Provider-specific direct image fields
        for image_obj in message.get("images") or []:
            image_url = image_obj.get("image_url") or image_obj.get("url")
            if not image_url:
                continue
            if image_url.startswith("data:image"):
                return _decode_data_url(image_url)
            return _download_image_from_url(image_url)

        content = message.get("content")
        if isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                image_url_obj = part.get("image_url")
                if isinstance(image_url_obj, dict) and image_url_obj.get("url"):
                    url = image_url_obj["url"]
                    if url.startswith("data:image"):
                        return _decode_data_url(url)
                    return _download_image_from_url(url)

                part_type = part.get("type")
                if part_type == "output_image" and part.get("image_base64"):
                    return base64.b64decode(part["image_base64"])

                if isinstance(part.get("text"), str):
                    text = part["text"]
                    # Handle markdown image links and plain URLs in text fallback.
                    md_match = re.search(r"!\[[^\]]*\]\((https?://[^)]+)\)", text)
                    if md_match:
                        return _download_image_from_url(md_match.group(1))
                    data_url_match = re.search(r"(data:image/[^\s\"]+)", text)
                    if data_url_match:
                        return _decode_data_url(data_url_match.group(1))
                    http_match = re.search(r"(https?://\S+)", text)
                    if http_match:
                        return _download_image_from_url(http_match.group(1).rstrip(").,;"))

        if isinstance(content, str):
            data_url_match = re.search(r"(data:image/[^\s\"]+)", content)
            if data_url_match:
                return _decode_data_url(data_url_match.group(1))
            http_match = re.search(r"(https?://\S+)", content)
            if http_match:
                return _download_image_from_url(http_match.group(1).rstrip(").,;"))

    raise RuntimeError("Model response did not include image data.")


def _get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY not set in environment."
        )
    return key


def _openrouter_headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME", "MetaFuse"),
    }


def _build_image_prompt(transcript: str, title: str | None, tags: list | None) -> str:
    """Ask Gemini text model (via OpenRouter) for a strong image prompt."""

    tags_str = ", ".join(tags) if tags else "none"
    clip = transcript[:_TRANSCRIPT_CHARS]

    system_instruction = (
        "You are a creative director specialising in YouTube thumbnails. "
        "Given a video transcript, title and tags, write a single, concise image-generation "
        "prompt (max 200 words) that describes a visually striking, professional thumbnail. "
        "Include: central subject, background, color palette, mood, text overlay suggestion "
        "(bold title text), and photorealistic or hyper-detailed illustration style. "
        "Output ONLY the prompt text, nothing else."
    )

    user_message = (
        f"Title: {title or 'Unknown'}\n"
        f"Tags: {tags_str}\n\n"
        f"Transcript excerpt:\n{clip}"
    )

    payload = {
        "model": _TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 300,
    }

    response = requests.post(
        f"{_OPENROUTER_BASE}/chat/completions",
        headers=_openrouter_headers(),
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def _build_image_prompt_fallback(transcript: str, title: str | None, tags: list | None) -> str:
    """Build a local prompt when provider prompt APIs are unavailable."""
    tags_str = ", ".join(tags[:8]) if tags else "cinematic, youtube thumbnail"
    transcript_clip = " ".join((transcript or "").split())[:400]
    return (
        f"YouTube thumbnail, 16:9 composition, ultra detailed, vibrant lighting, "
        f"high contrast, dramatic subject close-up, clean background separation, "
        f"bold readable title text area, professional content-creator style. "
        f"Topic title: {title or 'Viral Video'}. "
        f"Keywords: {tags_str}. "
        f"Context: {transcript_clip}"
    )


def _generate_image(prompt: str) -> bytes:
    """Generate an image via OpenRouter with endpoint fallbacks."""

    # Attempt 1: OpenAI-style image generation endpoint.
    image_payload = {
        "model": _IMAGE_MODEL,
        "prompt": prompt,
        "size": "1024x1024",
        "response_format": "b64_json",
    }
    image_response = requests.post(
        f"{_OPENROUTER_BASE}/images/generations",
        headers=_openrouter_headers(),
        json=image_payload,
        timeout=180,
    )
    if image_response.ok:
        return _extract_image_bytes_from_response(image_response.json())

    # Attempt 2: Chat-completions fallback for providers that don't expose /images.
    chat_payload = {
        "model": _IMAGE_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Generate a single high-quality image for the user's prompt.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ],
            },
        ],
    }
    chat_response = requests.post(
        f"{_OPENROUTER_BASE}/chat/completions",
        headers=_openrouter_headers(),
        json=chat_payload,
        timeout=180,
    )
    if chat_response.ok:
        return _extract_image_bytes_from_response(chat_response.json())

    # Attempt 3: Public image fallback to keep thumbnail UX working.
    # This avoids hard failure when an OpenRouter account or route is unavailable.
    fallback_url = (
        "https://image.pollinations.ai/prompt/"
        f"{quote_plus(prompt)}"
        "?width=1024&height=1024&nologo=true&model=flux"
    )
    fallback_resp = requests.get(fallback_url, timeout=180)
    fallback_resp.raise_for_status()
    return fallback_resp.content


def generate_thumbnail(
    video_id: int | None = None,
    transcript: str | None = None,
    title: str | None = None,
    tags: list | None = None,
) -> tuple[str | None, str | None, str]:
    """Generate a thumbnail for the given video.

    Parameters
    ----------
    video_id  : DB row id — used to fetch transcript (if not provided directly)
                and as the Cloudinary public_id key.
    transcript: Raw transcript text.  If None, fetched from DB via video_id.
    title     : Video title (optional, improves prompt quality).
    tags      : List of tag strings (optional).

    Returns
    -------
    (local_path, cloudinary_url, prompt_used)
      local_path     — path to the saved JPEG on disk, or None on failure.
      cloudinary_url — Cloudinary secure URL, or None if upload skipped.
      prompt_used    — the image-gen prompt (or an error message).
    """
    # 1. Resolve transcript
    if not transcript and video_id is not None:
        transcript = get_transcript(video_id)

    if not transcript:
        return None, None, "⚠️ No transcript available to generate thumbnail."

    try:
        # 2. Build vivid prompt
        prompt = _build_image_prompt(transcript, title=title, tags=tags)
    except Exception:
        prompt = _build_image_prompt_fallback(transcript, title=title, tags=tags)

    try:
        # 3. Generate image bytes
        image_bytes = _generate_image(prompt)
    except Exception as e:
        return None, None, f"⚠️ Image generation failed: {e}"

    # 4. Save to a temp file
    try:
        suffix = ".png"
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix,
            dir=Path(__file__).parent.parent / "data" / "outputs",
        )
        tmp.write(image_bytes)
        tmp.flush()
        local_path = tmp.name
        tmp.close()
    except Exception as e:
        return None, None, f"⚠️ Failed to save image locally: {e}"

    # 5. Upload to Cloudinary keyed by video_id
    cloudinary_url = None
    if video_id is not None:
        public_id = f"video_{video_id}"
        try:
            cloudinary_url, _ = upload_image(local_path, public_id=public_id)
        except Exception as e:
            print(f"  Cloudinary thumbnail upload failed: {e}")

    return local_path, cloudinary_url, prompt
