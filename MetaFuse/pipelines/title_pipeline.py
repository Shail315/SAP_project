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

Generate ONE SEO-optimized YouTube title (maximum 70 characters).
Return ONLY the title text — no quotes, no labels, nothing else.""")


def _get_llm():
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return ChatOpenAI(
        model=cfg["llm"]["model"],
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=cfg["llm"]["temperature"],
        max_tokens=cfg["llm"].get("max_tokens", 256),
    )


def generate_title(transcript, tags=None):
    """Return a single SEO-optimised YouTube title string."""
    llm = _get_llm()
    if not llm:
        return "N/A (API key not set)"
    try:
        msg = PROMPT.format_messages(
            transcript=transcript[:3000],
            tags=", ".join(tags) if tags else "N/A",
        )
        return llm.invoke(msg).content.strip().strip('"').strip("'")
    except Exception as e:
        return f"Error: {e}"
