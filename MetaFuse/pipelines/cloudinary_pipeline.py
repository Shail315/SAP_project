import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()


def _configure():
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )


def is_configured():
    return all([
        os.getenv("CLOUDINARY_CLOUD_NAME"),
        os.getenv("CLOUDINARY_API_KEY"),
        os.getenv("CLOUDINARY_API_SECRET"),
    ])


def upload_video(video_path, public_id=None):
    """Upload a video to Cloudinary.

    Returns (secure_url, public_id) on success, (None, None) otherwise.
    Uses upload_large to support files > 100 MB.
    """
    if not is_configured():
        return None, None
    _configure()
    try:
        result = cloudinary.uploader.upload_large(
            str(video_path),
            resource_type="video",
            public_id=public_id,
            folder="metafuse/videos",
            overwrite=True,
        )
        return result["secure_url"], result["public_id"]
    except Exception as e:
        print(f"  Cloudinary video upload failed: {e}")
        return None, None


def upload_audio(audio_path, public_id=None):
    """Upload an audio/WAV file to Cloudinary.

    Cloudinary treats audio under the 'video' resource_type.
    Returns (secure_url, public_id) on success, (None, None) otherwise.
    """
    if not is_configured():
        return None, None
    _configure()
    try:
        result = cloudinary.uploader.upload(
            str(audio_path),
            resource_type="video",
            public_id=public_id,
            folder="metafuse/audio",
            overwrite=True,
        )
        return result["secure_url"], result["public_id"]
    except Exception as e:
        print(f"  Cloudinary audio upload failed: {e}")
        return None, None


def upload_image(image_path, public_id=None):
    """Upload a thumbnail image to Cloudinary.

    Returns (secure_url, public_id) on success, (None, None) otherwise.
    """
    if not is_configured():
        return None, None
    _configure()
    try:
        result = cloudinary.uploader.upload(
            str(image_path),
            resource_type="image",
            public_id=public_id,
            folder="metafuse/thumbnails",
            overwrite=True,
        )
        return result["secure_url"], result["public_id"]
    except Exception as e:
        print(f"  Cloudinary image upload failed: {e}")
        return None, None
