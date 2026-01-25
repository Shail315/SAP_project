from pathlib import Path
import json

from utils.config_loader import load_config
from pipelines.audio_pipeline import split_audio
from pipelines.transcript_pipeline import transcribe
from pipelines.keyword_pipeline import extract_keywords
from pipelines.tag_pipeline import TagRanker
from pipelines.llm_pipeline import generate_metadata, refine_tags_with_llm


cfg = load_config()


def run():
    videos_dir = Path(cfg["paths"]["videos"])
    transcripts_dir = Path(cfg["paths"]["transcripts"])
    outputs_dir = Path(cfg["paths"]["outputs"])

    transcripts_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Initialize tag ranker
    tag_ranker = TagRanker()

    for video in videos_dir.glob("*.*"):
        print(f"\nProcessing {video.name}")
        print("="*60)

        # Step 1: Generate transcript (if not exists)
        out_file = transcripts_dir / f"{video.stem}.txt"
        if out_file.exists():
            print("Step 1: Loading existing transcript...")
            text = out_file.read_text()
            print(f"✓ Loaded transcript: {out_file}")
        else:
            print("Step 1: Transcribing audio...")
            chunks = split_audio(video)
            text = transcribe(chunks)
            out_file.write_text(text)
            print(f"✓ Transcript saved: {out_file}")

        # Step 2: Extract keywords using KeyBERT
        print("\nStep 2: Extracting keywords with keyword encoder...")
        keywords = extract_keywords(text, top_n=50)
        print(f"✓ Extracted {len(keywords)} keywords")

        # Step 3: Rank and select tags using custom keyword encoder model
        print("\nStep 3: Ranking tags with custom model...")
        raw_tags = tag_ranker.rank(text, keywords)
        print(f"✓ Selected top {len(raw_tags)} raw tags")

        # Step 4: Refine tags using LLM (based on transcript + raw tags)
        print("\nStep 4: Refining tags with LLM...")
        max_tags = cfg.get("tags", {}).get("max_tags", 10)
        tags = refine_tags_with_llm(text, raw_tags, max_tags=max_tags)
        print(f"✓ Refined to {len(tags)} high-quality tags")

        # Step 5: Generate description and caption using LLM
        print("\nStep 5: Generating metadata with LLM...")
        metadata = generate_metadata(text, tags)
        metadata["tags"] = tags
        metadata["raw_tags"] = raw_tags  # Keep raw tags for reference
        
        # Step 6: Save all outputs
        output_file = outputs_dir / f"{video.stem}_metadata.json"
        output_file.write_text(json.dumps(metadata, indent=2))
        print(f"✓ Metadata saved: {output_file}")
        
        # Display results
        print("\n" + "="*60)
        print("RESULTS:")
        print("="*60)
        print(f"\nTitle: {metadata.get('title', 'N/A')}")
        print(f"\nDescription: {metadata.get('description', 'N/A')}")
        print(f"\nCaption: {metadata.get('caption', 'N/A')}")
        print(f"\nTags ({len(tags)}): {', '.join(tags)}")
        print("\n" + "="*60)


if __name__ == "__main__":
    run()
