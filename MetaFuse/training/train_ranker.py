import ast
import os
from pathlib import Path
from typing import Iterable, List

import joblib
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression

DATA_PATH = Path("data/youtube_dataset/processed/train.csv")
MODEL_PATH = Path("models/tag_ranker.pkl")
MAX_ROWS = int(os.getenv("TRAIN_ROWS", "50000"))  # limit to keep memory reasonable
MAX_TAGS_PER_ROW = int(os.getenv("TAGS_PER_ROW", "5"))


def _parse_tags(val) -> List[str]:
    """Handle tags stored as list or string; fallback to empty list."""
    if isinstance(val, list):
        return [str(t) for t in val if t]
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return []
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return [str(t) for t in parsed if t]
        except (SyntaxError, ValueError):
            pass
        return [t for t in val.split("|") if t]
    return []


def _load_rows(path: Path, max_rows: int) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing training data at {path}")
    return pd.read_csv(path, low_memory=False, nrows=max_rows)


def _build_samples(df: pd.DataFrame) -> Iterable[tuple[str, int]]:
    for _, row in df.iterrows():
        tags = _parse_tags(row["tags"])[:MAX_TAGS_PER_ROW]
        text = str(row["text"])
        for tag in tags:
            yield f"{text} {tag}", 1


def main() -> None:
    df = _load_rows(DATA_PATH, MAX_ROWS)

    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    samples = list(_build_samples(df))
    if not samples:
        raise RuntimeError("No training samples constructed; check input data.")

    X = [s[0] for s in samples]
    y = [s[1] for s in samples]

    X_emb = embedder.encode(X, batch_size=16, show_progress_bar=True)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_emb, y)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print("Tag ranker trained & saved ->", MODEL_PATH)


if __name__ == "__main__":
    main()
