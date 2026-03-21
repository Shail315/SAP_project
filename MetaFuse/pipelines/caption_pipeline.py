import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from utils.config_loader import load_config

load_dotenv()
cfg = load_config()

PROMPT = ChatPromptTemplate.from_template("""You are a social media expert.

Transcript:
{transcript}

Write ONE engaging social-media caption (2 lines max, NO hashtags).
Return ONLY the caption text, nothing else.""")


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


def generate_caption(transcript, tags=None):
    """Return a short social-media caption string (no hashtags)."""
    llm = _get_llm()
    if not llm:
        return "N/A (API key not set)"
    try:
        msg = PROMPT.format_messages(transcript=transcript[:3000])
        return llm.invoke(msg).content.strip()
    except Exception as e:
        return f"Error: {e}"
