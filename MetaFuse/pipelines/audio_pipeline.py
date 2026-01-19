import subprocess
from pathlib import Path
from utils.config_loader import load_config

cfg = load_config()

def split_audio(video_path):
    out = Path(cfg["paths"]["audio_chunks"])
    out.mkdir(parents=True, exist_ok=True)

    subprocess.run([
        "ffmpeg", "-i", str(video_path),
        "-ac", "1", "-ar", "16000",
        "-f", "segment",
        "-segment_time", str(cfg["tagger"]["chunk_length"]),
        str(out / "chunk_%03d.wav")
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return sorted(out.glob("chunk_*.wav"))
