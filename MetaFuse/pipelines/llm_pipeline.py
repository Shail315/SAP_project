import os
import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from utils.config_loader import load_config

load_dotenv()
cfg = load_config()

def get_llm():
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    return ChatOpenAI(
        model=cfg["llm"]["model"],
        openai_api_key=api_key,
        base_url="https://models.github.ai/inference",
        temperature=cfg["llm"]["temperature"],
        max_tokens=cfg["llm"].get("max_tokens", 1024)
    )

# ─── Metadata prompt ────────────────────────────────────────────────────────────
PROMPT = ChatPromptTemplate.from_template("""You are a YouTube SEO expert.

Transcript:
{transcript}

Tags:
{tags}

Generate:
1. SEO optimized title (max 70 chars)
2. Detailed description (4-6 lines, include relevant keywords naturally)
3. Engaging caption for social media (2 lines max, NO hashtags)
4. 5-8 relevant hashtags (with # prefix, space-separated, e.g. #AI #MachineLearning)

Return JSON only with keys: title, description, caption, hashtags
""")

# ─── Tag refinement prompt ───────────────────────────────────────────────────────
TAG_REFINE_PROMPT = ChatPromptTemplate.from_template("""You are an expert at generating relevant tags for video content.

Transcript (for context):
{transcript}

Generated Tags (raw, may have duplicates, punctuation, or irrelevant items):
{raw_tags}

Your task:
1. Analyze the transcript to understand the main topics and themes
2. Review the generated tags and keep only the most relevant ones
3. Remove duplicates, consolidate similar tags (e.g., "AI Agent" and "AI Agents" → "AI Agents")
4. Remove punctuation marks, filler words, and noise
5. Add any important tags that are clearly missing based on the transcript
6. Return exactly {max_tags} high-quality, relevant tags

Return ONLY a JSON array of refined tags, nothing else. Example: ["tag1", "tag2", "tag3"]
""")

# ─── Chapter generation prompts ─────────────────────────────────────────────────
CHAPTERS_TIMED_PROMPT = ChatPromptTemplate.from_template("""You are an expert at creating YouTube chapter markers.

Below are timestamped transcript segments from a video:

{timed_transcript}

Your task:
1. Identify 3-8 distinct topic sections or logical breaks in the video
2. Use the real timestamps provided — pick the segment start time that best marks the beginning of each new section
3. Write concise, engaging chapter names (3-7 words each)
4. The very first chapter MUST start at 00:00

Return ONLY the chapters in this exact plain-text format (no markdown, no extra text):
00:00 Introduction
01:30 Chapter Title Here
03:15 Another Chapter Title
""")

CHAPTERS_TEXT_PROMPT = ChatPromptTemplate.from_template("""You are an expert at creating YouTube chapter markers.

Below is a transcript from a video:

{transcript}

The estimated video duration is roughly {estimated_duration} minutes.

Your task:
1. Identify 3-8 distinct topic sections in the transcript
2. Estimate plausible timestamps based on a uniform speaking pace and the content progression
3. Write concise, engaging chapter names (3-7 words each)
4. The very first chapter MUST start at 00:00

Return ONLY the chapters in this exact plain-text format (no markdown, no extra text):
00:00 Introduction
01:30 Chapter Title Here
03:15 Another Chapter Title
""")


# ─── Functions ──────────────────────────────────────────────────────────────────

def refine_tags_with_llm(transcript, raw_tags, max_tags=10):
    """Use LLM to refine and improve generated tags based on transcript context."""
    llm = get_llm()
    if not llm:
        # Fallback: basic cleaning if no LLM available
        cleaned = []
        for tag in raw_tags:
            clean_tag = re.sub(r'^[\W_]+|[\W_]+$', '', tag).strip()
            if clean_tag and len(clean_tag) > 2:
                cleaned.append(clean_tag)
        return cleaned[:max_tags]

    try:
        msg = TAG_REFINE_PROMPT.format_messages(
            transcript=transcript[:3000],
            raw_tags=", ".join(raw_tags),
            max_tags=max_tags
        )
        response = llm.invoke(msg).content

        try:
            tags = json.loads(response)
            if isinstance(tags, list):
                return [str(t).strip() for t in tags if t][:max_tags]
        except Exception:
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                tags = json.loads(json_match.group())
                return [str(t).strip() for t in tags if t][:max_tags]

        return raw_tags[:max_tags]
    except Exception as e:
        print(f"  Warning: LLM tag refinement failed: {e}")
        return raw_tags[:max_tags]


def generate_metadata(transcript, tags):
    llm = get_llm()
    if not llm:
        return {
            "title": "N/A (API key not set)",
            "description": "N/A (API key not set)",
            "caption": "N/A (API key not set)"
        }

    try:
        msg = PROMPT.format_messages(
            transcript=transcript[:3000],
            tags=", ".join(tags)
        )
        response = llm.invoke(msg).content

        try:
            return json.loads(response)
        except Exception:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            # Try to find raw JSON object without code fences
            obj_match = re.search(r'\{.*\}', response, re.DOTALL)
            if obj_match:
                return json.loads(obj_match.group())
            return {"title": "N/A", "description": "N/A", "caption": "N/A"}
    except Exception as e:
        return {
            "title": f"Error: {str(e)}",
            "description": f"Error: {str(e)}",
            "caption": f"Error: {str(e)}"
        }


def generate_chapters(timed_segments=None, transcript=None):
    """Generate YouTube chapter markers using the LLM.

    Pass `timed_segments` (list of {"start": float, "text": str}) when real
    Whisper timestamps are available (video upload flow).  Otherwise pass
    `transcript` (plain string) and chapters will be estimated.

    Returns a plain-text string of chapter lines, e.g.
        00:00 Introduction
        01:30 Topic Name
    """
    llm = get_llm()
    if not llm:
        return "⚠️ API key not set. Cannot generate chapters."

    try:
        if timed_segments:
            # Format segments as [MM:SS] text
            formatted_lines = []
            for seg in timed_segments:
                start = seg.get("start", 0)
                minutes = int(start // 60)
                seconds = int(start % 60)
                formatted_lines.append(f"[{minutes:02d}:{seconds:02d}] {seg['text']}")
            timed_text = "\n".join(formatted_lines[:200])  # cap to avoid token limit

            msg = CHAPTERS_TIMED_PROMPT.format_messages(timed_transcript=timed_text)
        else:
            # Estimate video duration from word count (~130 wpm average speaking pace)
            words = len(transcript.split()) if transcript else 1000
            est_minutes = max(1, round(words / 130))
            msg = CHAPTERS_TEXT_PROMPT.format_messages(
                transcript=transcript[:4000],
                estimated_duration=est_minutes
            )

        response = llm.invoke(msg).content
        return response.strip()

    except Exception as e:
        return f"Error generating chapters: {str(e)}"
