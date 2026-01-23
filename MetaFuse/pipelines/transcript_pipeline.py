import whisper
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
    texts = []
    for c in select_chunks(chunks):
        texts.append(model.transcribe(str(c), fp16=False)["text"])
    return " ".join(texts)
