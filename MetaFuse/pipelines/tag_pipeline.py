import joblib
from sentence_transformers import SentenceTransformer
from utils.config_loader import load_config

cfg = load_config()

class TagRanker:
    def __init__(self):
        self.model = joblib.load("models/tag_ranker.pkl")
        self.embedder = SentenceTransformer(cfg["models"]["embedding"])

    def rank(self, text, candidates):
        if not candidates:
            return []

        X = self.embedder.encode(
            [text + " " + c for c in candidates],
            batch_size=32
        )
        scores = self.model.predict_proba(X)[:, 1]
        ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
        return [t for t, _ in ranked[:cfg["tagger"]["top_k_tags"]]]
