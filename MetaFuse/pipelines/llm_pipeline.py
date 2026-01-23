import os
import json
import re
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
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
    llm = get_llm()
    if not llm:
        return {
            "title": "N/A (API key not set)",
            "description": "N/A (API key not set)",
            "caption": "N/A (API key not set)"
        }
    
    try:
        msg = PROMPT.format_messages(
            transcript=transcript[:2000],  # Limit transcript length
            tags=", ".join(tags)
        )
        response = llm.invoke(msg).content
        
        # Try to parse JSON from response
        try:
            return json.loads(response)
        except:
            # If LLM returns markdown-wrapped JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                return {
                    "title": "N/A",
                    "description": "N/A",
                    "caption": "N/A"
                }
    except Exception as e:
        return {
            "title": f"Error: {str(e)}",
            "description": f"Error: {str(e)}",
            "caption": f"Error: {str(e)}"
        }
