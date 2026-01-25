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

# Prompt for refining tags using LLM
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

def refine_tags_with_llm(transcript, raw_tags, max_tags=10):
    """Use LLM to refine and improve generated tags based on transcript context."""
    llm = get_llm()
    if not llm:
        # Fallback: basic cleaning if no LLM available
        cleaned = []
        for tag in raw_tags:
            # Remove punctuation and clean
            clean_tag = re.sub(r'^[\W_]+|[\W_]+$', '', tag).strip()
            if clean_tag and len(clean_tag) > 2:
                cleaned.append(clean_tag)
        return cleaned[:max_tags]
    
    try:
        msg = TAG_REFINE_PROMPT.format_messages(
            transcript=transcript[:3000],  # More context for better understanding
            raw_tags=", ".join(raw_tags),
            max_tags=max_tags
        )
        response = llm.invoke(msg).content
        
        # Parse JSON array from response
        try:
            tags = json.loads(response)
            if isinstance(tags, list):
                return [str(t).strip() for t in tags if t][:max_tags]
        except:
            # Try to extract JSON array from markdown
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                tags = json.loads(json_match.group())
                return [str(t).strip() for t in tags if t][:max_tags]
        
        # Fallback to original tags if parsing fails
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
            transcript=transcript[:2000],
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
