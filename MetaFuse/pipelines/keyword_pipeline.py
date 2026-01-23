from sentence_transformers import SentenceTransformer
import numpy as np

class KeywordGenerator:
    def __init__(self, model_path):
        self.model = SentenceTransformer(model_path)

    def generate(self, chunks, top_k=50):
        emb = self.model.encode(chunks)
        centroid = emb.mean(axis=0)
        scores = emb @ centroid
        idx = scores.argsort()[::-1][:top_k]
        return [chunks[i] for i in idx]
