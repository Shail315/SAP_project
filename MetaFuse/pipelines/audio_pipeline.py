import subprocess
from pathlib import Path
from utils.config_loader import load_config

cfg = load_config()


def split_audio(video_path):
    """Split `video_path` into audio chunks and return list of chunk Paths.

    Uses `configs/config.yaml` -> paths.audio_chunks and chunking.audio_chunk_seconds.
    """
    out = Path(cfg["paths"]["audio_chunks"]) / Path(video_path).stem
    out.mkdir(parents=True, exist_ok=True)

    # use configured audio chunk seconds (fallback to 30)
    seg_time = cfg.get("chunking", {}).get("audio_chunk_seconds", 30)

    subprocess.run([
        "ffmpeg", "-i", str(video_path),
        "-ac", "1", "-ar", "16000",
        "-f", "segment",
        "-segment_time", str(seg_time),
        str(out / "chunk_%03d.wav")
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    return sorted(out.glob("chunk_*.wav"))
