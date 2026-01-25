import joblib
from sentence_transformers import SentenceTransformer, util
import json
from pathlib import Path
from utils.config_loader import load_config

cfg = load_config()

# Model cache for reuse across runs
_model_cache = {}
_ranker_cache = None

def get_cached_model(model_name):
    """Get or create a cached SentenceTransformer model."""
    if model_name not in _model_cache:
        print(f"  Loading model: {model_name} (first time, will be cached)")
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]

def get_cached_ranker():
    """Get or create a cached ranker model."""
    global _ranker_cache
    if _ranker_cache is None and Path("models/tag_ranker.pkl").exists():
        print("  Loading tag ranker model (first time, will be cached)")
        _ranker_cache = joblib.load("models/tag_ranker.pkl")
    return _ranker_cache


class TagRanker:
    def __init__(self):
        # pretrained sklearn/joblib ranker (optional) - cached
        self.model = get_cached_ranker()
        # use configured keyword encoder - cached
        self.embedder = get_cached_model(cfg["models"].get("keyword_encoder"))

    def rank(self, text, candidates):
        if not candidates:
            return []

        X = self.embedder.encode(
            [text + " " + c for c in candidates],
            batch_size=32
        )
        if self.model is not None:
            scores = self.model.predict_proba(X)[:, 1]
            ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
            return [t for t, _ in ranked[: cfg.get("tags", {}).get("max_tags", 10)]]

        # fallback: simple embedding similarity ranking
        text_emb = self.embedder.encode(text)
        cand_embs = self.embedder.encode(candidates)
        sims = util.cos_sim(text_emb, cand_embs)[0]
        ranked = sorted(zip(candidates, sims.tolist()), key=lambda x: -x[1])
        return [t for t, _ in ranked[: cfg.get("tags", {}).get("max_tags", 10)]]
