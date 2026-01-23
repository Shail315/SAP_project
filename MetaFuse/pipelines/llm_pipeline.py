import os
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from utils.config_loader import Config

load_dotenv()
cfg = Config()

llm = ChatOpenAI(
    model=cfg["llm"]["model"],
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=cfg["llm"]["temperature"]
)

PROMPT = ChatPromptTemplate.from_template("""
You are a YouTube SEO expert.

Transcript:
{transcript}

Tags:
{tags}

Generate:
1. SEO optimized title (max 70 chars)
2. Short description (2 lines)
3. Engaging caption (1 line)

Return JSON only with keys:
title, description, caption
""")

def generate_metadata(transcript, tags):
    msg = PROMPT.format_messages(
        transcript=transcript,
        tags=", ".join(tags)
    )
    return llm(msg).content
