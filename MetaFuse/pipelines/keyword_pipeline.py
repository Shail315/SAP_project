from sentence_transformers import SentenceTransformer, util
from utils.config_loader import load_config
import numpy as np

cfg = load_config()

# Model cache for reuse across runs
_model_cache = {}

def get_cached_model(model_name):
    """Get or create a cached SentenceTransformer model."""
    if model_name not in _model_cache:
        print(f"  Loading model: {model_name} (first time, will be cached)")
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]

class KeywordExtractor:
    def __init__(self):
        self.model = get_cached_model(cfg["models"]["keyword_encoder"])
    
    def extract_keywords(self, text, top_n=50):
        # Split text into potential keywords (sentences and phrases)
        words = text.split()
        
        # Create n-gram candidates (1-3 words)
        candidates = []
        for i in range(len(words)):
            for n in range(1, 4):  # unigrams, bigrams, trigrams
                if i + n <= len(words):
                    phrase = ' '.join(words[i:i+n]).lower().strip()
                    if len(phrase) > 3:  # Filter very short phrases
                        candidates.append(phrase)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                unique_candidates.append(c)
        
        if not unique_candidates:
            return []
        
        # Encode text and candidates with custom model
        text_embedding = self.model.encode(text)
        candidate_embeddings = self.model.encode(unique_candidates)
        
        # Calculate cosine similarity
        similarities = util.cos_sim(text_embedding, candidate_embeddings)[0]
        
        # Get top keywords by similarity
        top_indices = similarities.argsort(descending=True)[:min(top_n, len(unique_candidates))]
        keywords = [unique_candidates[idx] for idx in top_indices.cpu().numpy()]
        
        return keywords

extractor = KeywordExtractor()

def extract_keywords(text, top_n=50):
    return extractor.extract_keywords(text, top_n)
