import joblib
from sentence_transformers import SentenceTransformer, util
import json
from pathlib import Path
from utils.config_loader import load_config

cfg = load_config()


class TagRanker:
    def __init__(self):
        # pretrained sklearn/joblib ranker (optional)
        self.model = joblib.load("models/tag_ranker.pkl") if Path("models/tag_ranker.pkl").exists() else None
        # use configured keyword encoder
        self.embedder = SentenceTransformer(cfg["models"].get("keyword_encoder"))

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
