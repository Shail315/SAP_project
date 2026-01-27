# MetaFuse 🎬

> **Intelligent Video Metadata Generation System**  
> Automated end-to-end pipeline for generating SEO-optimized titles, descriptions, captions, and tags from video content using state-of-the-art AI models.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Models & Technologies](#models--technologies)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Workflow](#workflow)
- [Technical Details](#technical-details)
- [Requirements](#requirements)
- [License](#license)

---

## 🎯 Overview

**MetaFuse** is an intelligent automation system designed to generate high-quality metadata for video content. It leverages cutting-edge AI models to process video files, extract meaningful insights, and produce SEO-optimized metadata including titles, descriptions, captions, and relevant tags. The system combines audio transcription, semantic keyword extraction, intelligent tag ranking, and large language model (LLM) based content generation in a unified pipeline.

The project is particularly useful for content creators, digital marketers, and media organizations looking to automate the tedious process of video metadata creation while maintaining professional quality standards.

---

## ✨ Key Features

- **🎙️ Automatic Transcription**: Converts video audio to text using OpenAI's Whisper model
- **🔑 Intelligent Keyword Extraction**: Uses KeyBERT with custom fine-tuned embeddings for accurate keyword identification
- **🏷️ Semantic Tag Ranking**: Employs a custom-trained SentenceBERT model for intelligent tag selection
- **🤖 AI-Powered Metadata Generation**: Generates SEO-optimized titles, descriptions, and captions using GPT-4o-mini
- **🎨 Interactive Web Interface**: User-friendly Gradio UI with two modes (video upload or transcript paste)
- **⚡ Batch Processing**: CLI tool for processing multiple videos automatically
- **💾 Model Caching**: Efficient resource management with intelligent model caching
- **📊 Structured Output**: JSON-formatted metadata for easy integration

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                              │
│                    Video File or Transcript                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUDIO PROCESSING LAYER                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Audio Extraction → Chunking (30s segments) → WAV Conv.  │  │
│  │  Tool: FFmpeg | Model: N/A                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TRANSCRIPTION LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Speech-to-Text Processing                                │  │
│  │  Model: OpenAI Whisper (Small)                            │  │
│  │  Output: Full text transcript                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 KEYWORD EXTRACTION LAYER                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Semantic Keyword Detection                               │  │
│  │  Model: Custom Fine-tuned SentenceBERT                    │  │
│  │  Base: all-MiniLM-L6-v2 (384-dim embeddings)              │  │
│  │  Training Data: YouTube Dataset (437,029 samples)         │  │
│  │  Method: N-gram candidates (1-3 words) + Cosine Sim.     │  │
│  │  Output: Top 50 keywords                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TAG RANKING LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Intelligent Tag Selection & Ranking                      │  │
│  │  Model: Custom Fine-tuned SentenceBERT                    │  │
│  │  Base: all-MiniLM-L6-v2 (384-dim embeddings)              │  │
│  │  Training: YouTube video-tag pairs dataset               │  │
│  │  Method: Semantic similarity scoring                      │  │
│  │  Output: Top 10 ranked tags (min score: 0.45)            │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  METADATA GENERATION LAYER                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SEO-Optimized Content Creation                           │  │
│  │  Model: GPT-4o-mini (OpenRouter API)                      │  │
│  │  Temperature: 0.3 | Max Tokens: 512                       │  │
│  │  Inputs: Transcript + Top Tags                            │  │
│  │  Outputs:                                                  │  │
│  │    • Title (max 70 chars, SEO-optimized)                  │  │
│  │    • Description (2 lines, engaging)                       │  │
│  │    • Caption (1 line, compelling)                          │  │
│  │    • Refined Tags (cleaned & validated)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OUTPUT LAYER                              │
│           JSON Metadata + Transcript Files                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Models & Technologies

<div align="center">

| Model | Purpose | Key Details |
|-------|---------|-------------|
| 🎙️ **OpenAI Whisper** | Audio Transcription | Multi-language support, robust to noise, handles various accents |
| ⭐ **Custom SentenceBERT** | Keyword Extraction & Tag Ranking | Fine-tuned on 437K YouTube samples, 384-dim embeddings |
| 🤖 **GPT-4o-mini** | Metadata Generation | SEO-optimized titles, descriptions, captions via OpenRouter |

</div>

### ⭐ Custom Keyword Encoder Model (Core Innovation)

**Architecture:**
```
SentenceTransformer(
  (0): Transformer (BertModel)        → Context understanding
  (1): Pooling (mean pooling)         → Sequence aggregation
  (2): Normalize                      → Unit vector normalization
)
```

**Training Specifications:**
- 🎯 **Base Model**: all-MiniLM-L6-v2 (sentence-transformers)
- 📊 **Dataset**: 437,029 YouTube video-tag-title pairs
- 🎓 **Training Method**: MultipleNegativesRankingLoss with contrastive learning
- 📏 **Output**: 384-dimensional dense vectors
- 📝 **Max Sequence**: 256 tokens
- 🎯 **Similarity**: Cosine similarity scoring

**Workflow:**
```python
1. Generate n-gram candidates (1-3 words) from transcript
2. Encode transcript → 384-dim embedding
3. Encode all candidates → 384-dim embeddings
4. Calculate cosine similarity scores
5. Rank by relevance & apply threshold (0.45)
6. Return top-10 tags
```

**Why This Model?**
- ✅ Trained specifically on YouTube content patterns
- ✅ Understands semantic relationships between video content and tags
- ✅ Fast inference (~5ms per encoding on GPU)
- ✅ Generalizes well to unseen content

### 🔧 Supporting Technologies

| Tool | Purpose |
|------|---------|
| **FFmpeg** | Audio extraction and chunking |
| **KeyBERT** | Initial keyword candidate generation |
| **LangChain** | LLM orchestration and prompt management |
| **Gradio** | Interactive web interface |
| **PyTorch** | Deep learning backend |

---

## 📁 Project Structure

```
MetaFuse/
├── app.py                          # Gradio web interface
├── main.py                         # CLI batch processing script
├── requirements.txt                # Python dependencies
├── LICENSE                         # Project license
├── README.md                       # This file
│
├── configs/
│   └── config.yaml                 # Central configuration file
│
├── data/
│   ├── videos/                     # Input video files
│   ├── audio_chunks/               # Temporary audio segments
│   ├── transcripts/                # Generated transcripts (.txt)
│   └── outputs/                    # Final metadata (.json)
│
├── models/
│   └── keyword_encoder/            # Custom SentenceBERT model
│       ├── config.json             # Model configuration
│       ├── model.safetensors       # Model weights
│       ├── vocab.txt               # Vocabulary file
│       ├── README.md               # Model documentation
│       ├── 1_Pooling/              # Pooling layer config
│       └── 2_Normalize/            # Normalization layer
│
├── pipelines/
│   ├── audio_pipeline.py           # Audio extraction & chunking
│   ├── transcript_pipeline.py      # Whisper transcription
│   ├── keyword_pipeline.py         # Keyword extraction
│   ├── tag_pipeline.py             # Tag ranking
│   └── llm_pipeline.py             # LLM metadata generation
│
└── utils/
    ├── config_loader.py            # Configuration management
    └── text_chunker.py             # Text processing utilities
```

---

## 🚀 Installation

### 📋 Prerequisites

| Requirement | Details |
|-------------|---------|
| 🐍 **Python** | 3.10 or higher |
| 🎬 **FFmpeg** | Audio processing (required) |
| 🎮 **GPU** | Optional (CUDA support for speed) |
| 🔑 **API Key** | OpenRouter or OpenAI |

### Quick Start

```bash
# 1️⃣ Clone repository
git clone https://github.com/Shail315/SAP_project.git
cd SAP_project/MetaFuse

# 2️⃣ Install FFmpeg
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows: Download from ffmpeg.org and add to PATH

# 3️⃣ Install Python dependencies
pip install -r requirements.txt

# 4️⃣ Set up API key
echo "OPENROUTER_API_KEY=your_key_here" > .env
# OR use: OPENAI_API_KEY=your_key_here

# 🚀 Run!
python app.py  # Web UI
# OR
python main.py # Batch processing
```

<details>
<summary><b>📦 Key Dependencies</b></summary>

- `openai-whisper` - Audio transcription
- `torch` - Deep learning framework
- `sentence-transformers` - Embeddings & semantic search
- `keybert` - Keyword extraction
- `langchain-openai` - LLM integration
- `gradio` - Web interface
- `python-dotenv` - Environment management

</details>

<details>
<summary><b>🔑 Get API Keys</b></summary>

- **OpenRouter** (recommended): [openrouter.ai](https://openrouter.ai/)
- **OpenAI**: [platform.openai.com](https://platform.openai.com/)

</details>

---

## ⚙️ Configuration

Edit `configs/config.yaml` to customize the pipeline:

```yaml
paths:
  videos: "data/videos"              # Input video directory
  audio_chunks: "data/audio_chunks"  # Temporary audio storage
  transcripts: "data/transcripts"    # Transcript output directory
  outputs: "data/outputs"            # Metadata output directory

models:
  whisper: "small"                   # Whisper model size: tiny, base, small, medium, large
  keyword_encoder: "models/keyword_encoder"  # Path to custom SentenceBERT

chunking:
  audio_chunk_seconds: 30            # Audio segment length
  transcript_chunk_words: 300        # Text chunk size for processing

tags:
  max_tags: 10                       # Maximum number of tags to generate
  min_score: 0.45                    # Minimum similarity score for tag selection

llm:
  provider: "openrouter"             # LLM provider
  model: "openai/gpt-4o-mini"        # Model identifier
  temperature: 0.3                   # Generation creativity (0.0-1.0)
  max_tokens: 512                    # Maximum response length
```

---

## 💻 Usage

<table>
<tr>
<td width="50%" valign="top">

### 🌐 Option 1: Web Interface

```bash
cd MetaFuse
python app.py
```

**Features:**
- 📹 **Video Upload** - Process MP4, AVI, MOV files
- 📝 **Transcript Input** - Skip to keyword extraction
- 🎨 Professional purple/white UI
- ⚡ Real-time processing & results

🌐 **Access:** `http://127.0.0.1:7860`

</td>
<td width="50%" valign="top">

### ⚙️ Option 2: Batch Processing

```bash
cd MetaFuse
python main.py
```

**Workflow:**
1. Scans `data/videos/` directory
2. Processes all videos automatically
3. Saves transcripts (.txt)
4. Saves metadata (.json)
5. Smart caching for efficiency

</td>
</tr>
</table>

### 📤 Output Structure

```json
{
  "title": "SEO-Optimized Video Title (max 70 chars)",
  "description": "Engaging 2-line description with key info.",
  "caption": "Compelling one-liner! 🚀",
  "tags": ["keyword1", "keyword2", "keyword3", ...],
  "transcript": "Full video transcript..."
}
```

---

## 🔄 Workflow

### Complete Processing Pipeline

```
┌──────────────────┐
│  Video File      │
│  or Transcript   │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Step 1: Audio Extraction           │
│  ─────────────────────────────────  │
│  • Extract audio track              │
│  • Split into 30-second chunks      │
│  • Convert to WAV format            │
│  Tool: FFmpeg                       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Step 2: Transcription              │
│  ─────────────────────────────────  │
│  • Process each audio chunk         │
│  • Convert speech to text           │
│  • Concatenate all segments         │
│  Model: Whisper (Small)             │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Step 3: Keyword Extraction         │
│  ─────────────────────────────────  │
│  • Generate n-gram candidates       │
│  • Encode with custom SentenceBERT │
│  • Calculate similarity scores      │
│  • Select top 50 keywords           │
│  Model: Custom keyword_encoder      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Step 4: Tag Ranking                │
│  ─────────────────────────────────  │
│  • Rank keywords by relevance       │
│  • Apply similarity threshold       │
│  • Select top 10 tags               │
│  Model: Custom keyword_encoder      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Step 5: Metadata Generation        │
│  ─────────────────────────────────  │
│  • Generate SEO-optimized title     │
│  • Create engaging description      │
│  • Craft compelling caption         │
│  • Refine and clean tags            │
│  Model: GPT-4o-mini                 │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Output: JSON Metadata              │
│  • title, description, caption      │
│  • tags, transcript                 │
└─────────────────────────────────────┘
```

### Performance Optimization

- **Model Caching**: All models are loaded once and cached for subsequent runs
- **Transcript Reuse**: Existing transcripts are loaded instead of re-transcribing
- **⚡ Performance Optimizations

| Feature | Benefit |
|---------|---------|
| 💾 **Model Caching** | Load once, reuse across runs |
| 📝 **Transcript Reuse** | Skip re-transcription if exists |
| 📦 **Batch Encoding** | Process keywords efficiently |
| ✂️ **Chunked Processing** | Handle large files smoothly |

### 🎯 Model Training Pipeline

<table>
<tr>
<td width="50%">

**Data Preprocessing**
```
437,029 YouTube samples
    ↓
Text cleaning & normalization
    ↓
Duplicate removal
    ↓
Category balancing
```

</td>
<td width="50%">

**Training Process**
```
all-MiniLM-L6-v2 base
    ↓
MultipleNegativesRankingLoss
    ↓
Contrastive learning
    ↓
Video-tag optimization
```

</td>
</tr>
</table>

### 🎨 LLM Prompt Engineering

Our carefully crafted prompts ensure professional, SEO-optimized outputs:

| Output Type | Specification | Optimization Focus |
|-------------|--------------|-------------------|
| **Title** | Max 70 chars | SEO keywords, click-worthy |
| **Description** | 2 lines | Engaging hook, key information |
| **Caption** | 1 line | Compelling, action-oriented |
| **Tags** | Top 10 | Cleaned, validated, relevant |

---

## 📦 Requirements

### Minimum System Requirements

- **CPU**: Quad-core processor (Intel i5 or equivalent)
- **RAM**: 8 GB
- **Storage**: 5 GB free space
- **Internet**: Required for LLM API calls

### Recommended System Requirements

- **� System Requirements

<table>
<tr>
<td width="50%">

### 📊 Minimum Specs
- **CPU**: Quad-core (Intel i5)
- **RAM**: 8 GB
- **Storage**: 5 GB
- **Internet**: Required for API

</td>
<td width="50%">

### 🚀 Recommended Specs
- **CPU**: Octa-core (Intel i7)
- **RAM**: 16 GB
- **GPU**: NVIDIA 4GB+ VRAM
- **Storage**: 10 GB
- **Internet**: Broadband

</td>
</tr>
</table>
```json
{
  "title": "Honest Review: XYZ Smartphone - Best Budget Phone of 2026?",
  "description": "Complete hands-on review of the XYZ smartphone covering design, performance, camera quality, and battery life. Is it worth your money?",
  "caption": "The budget smartphone that punches above its weight! 🚀",
  "tags": [
    "smartphone review",
    "budget phone",
    "tech review",
    "xyz smartphone",
    "mobile phone",
    "camera test",
    "battery life",
    "performance test",
    "unboxing",
    "2026 phones"
  ]
}
```

---

## 🛠️ Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| ❌ **FFmpeg not found** | `sudo apt install ffmpeg` (Linux) or `brew install ffmpeg` (macOS) |
| ⚠️ **CUDA out of memory** | Edit `config.yaml` → set `device: "cpu"` |
| 🔑 **API key error** | Check `.env` file exists with valid key, restart app |
| 📥 **Model download fails** | Ensure internet connection, check `~/.cache/huggingface/` |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

