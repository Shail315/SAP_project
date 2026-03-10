"""Thumbnail pipeline — generates a YouTube-style thumbnail using Gemini image
generation and stores it in Cloudinary, keyed by video_id for easy retrieval.

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
import base64
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

from utils.db import get_transcript
from pipelines.cloudinary_pipeline import upload_image

load_dotenv()

# ── Gemini model names ──────────────────────────────────────────────────────
_TEXT_MODEL  = "gemini-2.5-flash-lite"                       # prompt builder
_IMAGE_MODEL = "gemini-2.5-flash-image"  # image generator

# ── Max characters of transcript fed to Gemini (keep cost low) ─────────────
_TRANSCRIPT_CHARS = 3000


def _get_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise EnvironmentError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) not set in environment."
        )
    return key


def _build_image_prompt(transcript: str, title: str | None, tags: list | None) -> str:
    """Ask Gemini text model to craft a detailed image-generation prompt."""
    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel(_TEXT_MODEL)

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

    response = model.generate_content(
        [system_instruction, user_message],
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=300,
            temperature=0.7,
        ),
    )
    return response.text.strip()


def _generate_image(prompt: str) -> bytes:
    """Call Gemini image-generation model; return raw PNG/JPEG bytes."""
    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel(_IMAGE_MODEL)

    response = model.generate_content(
        prompt,
        generation_config={"response_modalities": ["IMAGE", "TEXT"]},
    )

    # The image is returned as an inline blob inside candidates[0].content.parts
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data is not None:
            return part.inline_data.data  # already bytes

    raise RuntimeError("Gemini did not return an image in its response.")


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
    except Exception as e:
        return None, None, f"⚠️ Prompt generation failed: {e}"

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
