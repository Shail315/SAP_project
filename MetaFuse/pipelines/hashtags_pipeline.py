import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from utils.config_loader import load_config

load_dotenv()
cfg = load_config()

PROMPT = ChatPromptTemplate.from_template("""You are a YouTube SEO expert.

Transcript:
{transcript}

Tags:
{tags}

Generate 5-8 highly relevant hashtags with the # prefix, space-separated
(e.g. #AI #MachineLearning).
Return ONLY the hashtags on one line, nothing else.""")


def _get_llm():
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return ChatOpenAI(
        model=cfg["llm"]["model"],
        openai_api_key=api_key,
        base_url="https://models.github.ai/inference",
        temperature=cfg["llm"]["temperature"],
        max_tokens=cfg["llm"].get("max_tokens", 128),
    )


def generate_hashtags(transcript, tags=None):
    """Return a space-separated hashtag string (e.g. '#AI #Python')."""
    llm = _get_llm()
    if not llm:
        return "N/A (API key not set)"
    try:
        msg = PROMPT.format_messages(
            transcript=transcript[:3000],
            tags=", ".join(tags) if tags else "N/A",
        )
        return llm.invoke(msg).content.strip()
    except Exception as e:
        return f"Error: {e}"
