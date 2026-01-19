from keybert import KeyBERT
from sentence_transformers import SentenceTransformer

kw = KeyBERT(SentenceTransformer("all-MiniLM-L6-v2"))

def extract_keywords(text, top_n=20):
    return [k for k, _ in kw.extract_keywords(
        text, top_n=top_n, use_mmr=True, diversity=0.7
    )]
