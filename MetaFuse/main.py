from pathlib import Path
from utils.cache import cache_key, load_cache, save_cache
from pipelines.audio_pipeline import split_audio
from pipelines.transcript_pipeline import transcribe
from pipelines.keyword_pipeline import extract_keywords
from pipelines.tag_pipeline import TagRanker
from utils.config_loader import load_config

cfg = load_config()
ranker = TagRanker()

for video in Path(cfg["paths"]["videos"]).glob("*.*"):
    print(f"\nProcessing {video.name}")

    key = cache_key(video)
    text = load_cache(key)

    if not text:
        chunks = split_audio(video)
        text = transcribe(chunks)
        save_cache(key, text)

    keywords = extract_keywords(text)
    tags = ranker.rank(text, keywords)

    print("Generated Tags:", tags)
