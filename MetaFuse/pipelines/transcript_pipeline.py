import whisper
from pathlib import Path
from utils.config_loader import load_config

cfg = load_config()
model = whisper.load_model(cfg["models"]["whisper"])


def select_chunks(chunks):
    # optional limit for number of chunks to transcribe; if not set, use all
    max_chunks = cfg.get("chunking", {}).get("max_chunks")
    if not max_chunks:
        return chunks
    if len(chunks) <= max_chunks:
        return chunks
    step = max(1, len(chunks) // max_chunks)
    return [chunks[i] for i in range(0, len(chunks), step)][:max_chunks]


def transcribe(chunks):
    """Transcribe audio chunks and return (full_text, timed_segments).

    timed_segments is a list of {"start": float_seconds, "text": str}
    with timestamps adjusted to absolute video time.
    """
    texts = []
    timed_segments = []
    seg_time = cfg.get("chunking", {}).get("audio_chunk_seconds", 30)

    for c in select_chunks(chunks):
        chunk_path = Path(c)
        # Derive chunk index from filename (chunk_000.wav → 0) to compute
        # the absolute time offset within the original video.
        try:
            chunk_index = int(chunk_path.stem.split("_")[-1])
        except ValueError:
            chunk_index = 0
        offset = chunk_index * seg_time

        result = model.transcribe(str(c), fp16=False)
        texts.append(result["text"])

        for seg in result.get("segments", []):
            timed_segments.append({
                "start": offset + seg["start"],
                "text": seg["text"].strip()
            })

    return " ".join(texts), timed_segments
