import shutil
import gradio as gr
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.config_loader import load_config
from utils.db import (
    init_db, save_video, save_transcript, save_audio_chunk,
    get_transcript, upsert_metadata,
)
from pipelines.audio_pipeline import split_audio
from pipelines.transcript_pipeline import transcribe
from pipelines.keyword_pipeline import extract_keywords
from pipelines.tag_pipeline import TagRanker
from pipelines.llm_pipeline import refine_tags_with_llm, generate_chapters
from pipelines.title_pipeline import generate_title
from pipelines.description_pipeline import generate_description
from pipelines.caption_pipeline import generate_caption
from pipelines.hashtags_pipeline import generate_hashtags
from pipelines.cloudinary_pipeline import (
    upload_video as cld_upload_video,
    upload_audio as cld_upload_audio,
    upload_image as cld_upload_image,
)
from pipelines.thumbnail_pipeline import generate_thumbnail

# ─── Boot ─────────────────────────────────────────────────────────────────────
init_db()
cfg = load_config()

_tag_ranker = None


def get_tag_ranker():
    global _tag_ranker
    if _tag_ranker is None:
        _tag_ranker = TagRanker()
    return _tag_ranker

# Custom CSS for purple/white theme with larger text
custom_css = """
/* Main theme colors */
:root {
    --primary-color: #7C3AED;
    --primary-hover: #6D28D9;
    --primary-light: #A78BFA;
    --bg-color: #FFFFFF;
    --bg-secondary: #F5F3FF;
    --text-primary: #1F2937;
    --text-secondary: #6B7280;
    --border-color: #E9D5FF;
}

/* Global styles */
.gradio-container {
    background: linear-gradient(135deg, #F5F3FF 0%, #FFFFFF 50%, #F5F3FF 100%) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Header styling */
.main-header {
    text-align: center;
    padding: 2rem 1rem;
    background: linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%);
    border-radius: 16px;
    margin-bottom: 2rem;
    box-shadow: 0 10px 40px rgba(124, 58, 237, 0.3);
}

.main-header h1 {
    color: white !important;
    font-size: 3rem !important;
    font-weight: 800 !important;
    margin-bottom: 0.5rem !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.main-header p {
    color: rgba(255,255,255,0.9) !important;
    font-size: 1.25rem !important;
    margin: 0 !important;
}

/* Tab styling */
.tabs {
    background: white !important;
    border-radius: 12px !important;
    padding: 0.5rem !important;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.1) !important;
}

button.selected {
    background: linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
}

/* Input/Output boxes */
.input-box, .output-box {
    border: 2px solid #E9D5FF !important;
    border-radius: 12px !important;
    font-size: 1.1rem !important;
}

textarea, input[type="text"] {
    font-size: 1.1rem !important;
    line-height: 1.6 !important;
}

/* Labels */
label {
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    color: #7C3AED !important;
}

/* Primary button */
.primary-btn, button.primary {
    background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%) !important;
    color: white !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    padding: 1rem 2rem !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4) !important;
    transition: all 0.3s ease !important;
}

.primary-btn:hover, button.primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5) !important;
}

/* Secondary / regenerate button */
.secondary-btn, button.secondary {
    background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%) !important;
    color: #7C3AED !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    padding: 0.8rem 1.5rem !important;
    border-radius: 12px !important;
    border: 2px solid #A78BFA !important;
    transition: all 0.3s ease !important;
}

.secondary-btn:hover, button.secondary:hover {
    background: linear-gradient(135deg, #EDE9FE 0%, #DDD6FE 100%) !important;
    transform: translateY(-1px) !important;
}

/* Chapter button */
.chapter-btn {
    background: linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%) !important;
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    padding: 0.8rem 1.5rem !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4) !important;
    transition: all 0.3s ease !important;
}

.chapter-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(14, 165, 233, 0.5) !important;
}

/* Chapters output */
.chapters-display textarea {
    font-size: 1.15rem !important;
    font-family: 'Courier New', monospace !important;
    color: #1F2937 !important;
    line-height: 1.8 !important;
}

/* Result cards */
.result-card {
    background: white;
    border: 2px solid #E9D5FF;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 0.75rem 0;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.08);
}

/* Section headers */
.section-header {
    color: #7C3AED;
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #E9D5FF;
}

/* Video upload area */
.upload-area {
    border: 3px dashed #A78BFA !important;
    border-radius: 16px !important;
    background: #F5F3FF !important;
    min-height: 200px !important;
}

/* Progress bar */
.progress-bar {
    background: #E9D5FF !important;
}

.progress-bar > div {
    background: linear-gradient(90deg, #7C3AED 0%, #A78BFA 100%) !important;
}

/* Footer */
.footer-text {
    text-align: center;
    color: #6B7280;
    font-size: 1rem;
    padding: 1.5rem;
    margin-top: 2rem;
}

/* Larger text for outputs */
.large-text textarea {
    font-size: 1.2rem !important;
    line-height: 1.7 !important;
}

/* Tags display */
.tags-display textarea {
    font-size: 1.15rem !important;
    color: #7C3AED !important;
    font-weight: 500 !important;
}

/* Individual generate buttons */
.gen-btn {
    background: linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%) !important;
    color: white !important;
    font-size: .9rem !important;
    font-weight: 600 !important;
    padding: .55rem 1rem !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100% !important;
    box-shadow: 0 3px 10px rgba(124,58,237,.35) !important;
}

/* Regenerate / DB button */
.regen-btn {
    background: linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%) !important;
    color: white !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    padding: .8rem 1.6rem !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(14,165,233,.4) !important;
}

/* Status box */
.status-box textarea {
    font-size: 1rem !important;
    background: #F5F3FF !important;
    color: #374151 !important;
}

/* Horizontal rule between sections */
.section-divider { border-top: 2px solid #E9D5FF; margin: 1.2rem 0; }
"""



# ─── Shared helpers ────────────────────────────────────────────────────────────

def _extract_raw_tags(transcript_text):
    keywords = extract_keywords(transcript_text, top_n=50)
    return get_tag_ranker().rank(transcript_text, keywords)


def _chapters_wrapper(segments, transcript):
    if segments:
        return generate_chapters(timed_segments=segments)
    return generate_chapters(transcript=transcript)


# ─── Video Tab – Process ──────────────────────────────────────────────────────

def process_video(video_file, progress=gr.Progress()):
    """Upload to Cloudinary, split audio, transcribe, persist everything to SQLite."""
    if video_file is None:
        return ("⚠️ Please upload a video file.", "", None, [], [], "",
                gr.update(visible=False))
    try:
        video_path = Path(video_file)

        # Copy to persistent local storage
        progress(0.05, desc="Saving video locally…")
        local_dir = Path(cfg["paths"]["videos"])
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / video_path.name
        shutil.copy2(video_path, local_path)

        # Upload video to Cloudinary
        video_url, video_pid = cld_upload_video(local_path)
        cld_video_msg = (f"☁️ Video → {video_url}" if video_url
                         else "⚠️ Cloudinary not configured — video stored locally only")

        # Create DB record
        video_id = save_video(
            video_path.name,
            local_path=str(local_path),
            cloudinary_video_url=video_url,
            cloudinary_video_public_id=video_pid,
        )

        # Split audio with ffmpeg
        progress(0.25, desc="Splitting audio with ffmpeg…")
        chunks = split_audio(local_path)

        # Upload audio chunks to Cloudinary
        uploaded_audio = 0
        for chunk in chunks:
            url, pid = cld_upload_audio(chunk)
            save_audio_chunk(video_id, chunk.name, url, pid)
            if url:
                uploaded_audio += 1
        cld_audio_msg = (
            f"☁️ {uploaded_audio}/{len(chunks)} audio chunk(s) uploaded"
            if uploaded_audio else "⚠️ Audio chunks stored locally only"
        )

        # Transcribe
        progress(0.55, desc="Transcribing with Whisper…")
        transcript, timed_segments = transcribe(chunks)

        if not transcript or not transcript.strip():
            return ("❌ Transcription failed — check the video file.",
                    "", video_id, [], [], str(local_path), gr.update(visible=False))

        save_transcript(video_id, transcript)

        # Extract raw keywords (fast, no LLM)
        progress(0.90, desc="Extracting initial keywords…")
        raw_tags = _extract_raw_tags(transcript)

        progress(1.0, desc="✅ Processing complete!")
        status = (f"✅ Processed  |  DB ID: {video_id}\n"
                  f"{cld_video_msg}\n{cld_audio_msg}")
        return (status, transcript, video_id, timed_segments, raw_tags,
                str(local_path), gr.update(visible=True))

    except Exception as e:
        return (f"❌ Error: {e}", "", None, [], [], "", gr.update(visible=False))


# ─── Individual pipeline handlers ─────────────────────────────────────────────

def gen_tags(video_id, transcript, raw_tags, progress=gr.Progress()):
    if not video_id:
        return "⚠️ Process a video first.", []
    progress(0.3, desc="Refining tags with AI…")
    max_tags = cfg.get("tags", {}).get("max_tags", 10)
    refined = refine_tags_with_llm(transcript, raw_tags, max_tags=max_tags)
    upsert_metadata(video_id, tags=", ".join(refined))
    progress(1.0, desc="✅ Tags saved!")
    return ", ".join(refined), refined


def gen_title(video_id, transcript, tags_list, progress=gr.Progress()):
    if not video_id:
        return "⚠️ Process a video first."
    progress(0.3, desc="Generating title…")
    title = generate_title(transcript, tags_list or [])
    upsert_metadata(video_id, title=title)
    progress(1.0, desc="✅ Title saved!")
    return title


def gen_description(video_id, transcript, tags_list, progress=gr.Progress()):
    if not video_id:
        return "⚠️ Process a video first."
    progress(0.3, desc="Generating description…")
    desc = generate_description(transcript, tags_list or [])
    upsert_metadata(video_id, description=desc)
    progress(1.0, desc="✅ Description saved!")
    return desc


def gen_caption(video_id, transcript, tags_list, progress=gr.Progress()):
    if not video_id:
        return "⚠️ Process a video first."
    progress(0.3, desc="Generating caption…")
    caption = generate_caption(transcript, tags_list or [])
    upsert_metadata(video_id, caption=caption)
    progress(1.0, desc="✅ Caption saved!")
    return caption


def gen_hashtags(video_id, transcript, tags_list, progress=gr.Progress()):
    if not video_id:
        return "⚠️ Process a video first."
    progress(0.3, desc="Generating hashtags…")
    hashtags = generate_hashtags(transcript, tags_list or [])
    upsert_metadata(video_id, hashtags=hashtags)
    progress(1.0, desc="✅ Hashtags saved!")
    return hashtags


def gen_chapters(video_id, transcript, segments, progress=gr.Progress()):
    if not video_id:
        return "⚠️ Process a video first."
    progress(0.3, desc="Generating chapters…")
    chapters = _chapters_wrapper(segments, transcript)
    upsert_metadata(video_id, chapters=chapters)
    progress(1.0, desc="✅ Chapters saved!")
    return chapters


def gen_thumbnail(video_id, title, transcript, tags_list, progress=gr.Progress()):
    if not video_id:
        return None, "⚠️ Process a video first."
    progress(0.2, desc="Building image prompt from transcript…")
    # generate_thumbnail fetches transcript from DB if not supplied,
    # generates the image via Gemini, and uploads to Cloudinary automatically.
    thumb_img, cloudinary_url, prompt_used = generate_thumbnail(
        video_id=video_id,
        transcript=transcript or None,
        title=title or None,
        tags=tags_list or None,
    )
    if thumb_img:
        upsert_metadata(video_id,
                        thumbnail_url=cloudinary_url or "",
                        thumbnail_local_path=thumb_img)
    progress(1.0, desc="✅ Thumbnail ready!")
    return thumb_img, prompt_used


# ─── Generate All (parallel / streaming) ──────────────────────────────────────

def generate_all_video(video_id, transcript, raw_tags, segments, video_path,
                       progress=gr.Progress()):
    """Run all pipelines in parallel; yield partial outputs as each finishes."""
    empty = ("", "", "", "", "", "", None, "", [])
    if not video_id:
        yield empty
        return

    results = {k: "" for k in ["tags", "title", "description",
                                "caption", "hashtags", "chapters"]}
    results.update({"thumb_img": None, "thumb_desc": ""})
    tags_list = []

    # Step 1 — refine tags (others depend on them)
    progress(0.10, desc="Refining tags…")
    max_tags = cfg.get("tags", {}).get("max_tags", 10)
    try:
        tags_list = refine_tags_with_llm(transcript, raw_tags, max_tags=max_tags)
        results["tags"] = ", ".join(tags_list)
        upsert_metadata(video_id, tags=results["tags"])
    except Exception as e:
        tags_list = (raw_tags or [])[:max_tags]
        results["tags"] = f"Error: {e}"

    progress(0.22, desc="Tags ready — launching parallel pipelines…")
    yield (results["tags"], results["title"], results["description"],
           results["caption"], results["hashtags"], results["chapters"],
           results["thumb_img"], results["thumb_desc"], tags_list)

    # Step 2 — everything else in parallel
    futures_map = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures_map[executor.submit(generate_title,       transcript, tags_list)] = "title"
        futures_map[executor.submit(generate_description, transcript, tags_list)] = "description"
        futures_map[executor.submit(generate_caption,     transcript, tags_list)] = "caption"
        futures_map[executor.submit(generate_hashtags,    transcript, tags_list)] = "hashtags"
        futures_map[executor.submit(_chapters_wrapper, segments, transcript)]     = "chapters"
        futures_map[executor.submit(
            generate_thumbnail,
            video_id, transcript,
            results.get("title", ""), tags_list,
        )] = "thumbnail"

        completed = 0
        n = len(futures_map)
        for future in as_completed(futures_map):
            key = futures_map[future]
            try:
                value = future.result()
                if key == "thumbnail":
                    results["thumb_img"], cloudinary_url, results["thumb_desc"] = value
                    if results["thumb_img"]:
                        upsert_metadata(video_id,
                                        thumbnail_url=cloudinary_url or "",
                                        thumbnail_local_path=results["thumb_img"])
                else:
                    results[key] = value
                    upsert_metadata(video_id, **{key: results[key]})
            except Exception as e:
                if key == "thumbnail":
                    results["thumb_desc"] = f"Error: {e}"
                else:
                    results[key] = f"Error: {e}"

            completed += 1
            progress(0.22 + (completed / n) * 0.78,
                     desc=f"✅ {key} complete ({completed}/{n})")
            yield (results["tags"], results["title"], results["description"],
                   results["caption"], results["hashtags"], results["chapters"],
                   results["thumb_img"], results["thumb_desc"], tags_list)


# ─── Regenerate All from DB ────────────────────────────────────────────────────

def regenerate_all_video(video_id, segments, video_path, progress=gr.Progress()):
    """Fetch stored transcript from SQLite and regenerate all metadata."""
    if not video_id:
        yield ("",) * 10
        return
    transcript = get_transcript(video_id)
    if not transcript:
        yield ("⚠️ No transcript in database.",) + ("",) * 9
        return
    raw_tags = _extract_raw_tags(transcript)
    for partial in generate_all_video(video_id, transcript, raw_tags,
                                      segments, video_path, progress):
        yield (transcript,) + partial


# ─── Paste Transcript Tab ──────────────────────────────────────────────────────

def process_transcript_tab(text, progress=gr.Progress()):
    if not text or not text.strip():
        return "⚠️ Please paste a transcript.", None, [], gr.update(visible=False)
    progress(0.5, desc="Extracting keywords…")
    raw_tags = _extract_raw_tags(text)
    video_id = save_video("(pasted transcript)", local_path=None)
    save_transcript(video_id, text)
    progress(1.0, desc="✅ Ready!")
    return f"✅ Stored  |  DB ID: {video_id}", video_id, raw_tags, gr.update(visible=True)


def generate_all_transcript(video_id, transcript, raw_tags, progress=gr.Progress()):
    empty = ("", "", "", "", "", "", [])
    if not video_id:
        yield empty
        return

    results = {k: "" for k in ["tags", "title", "description",
                                "caption", "hashtags", "chapters"]}
    tags_list = []

    progress(0.10, desc="Refining tags…")
    max_tags = cfg.get("tags", {}).get("max_tags", 10)
    try:
        tags_list = refine_tags_with_llm(transcript, raw_tags, max_tags=max_tags)
        results["tags"] = ", ".join(tags_list)
        upsert_metadata(video_id, tags=results["tags"])
    except Exception as e:
        tags_list = (raw_tags or [])[:max_tags]
        results["tags"] = f"Error: {e}"

    progress(0.22, desc="Launching parallel pipelines…")
    yield (results["tags"], results["title"], results["description"],
           results["caption"], results["hashtags"], results["chapters"], tags_list)

    futures_map = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures_map[executor.submit(generate_title,       transcript, tags_list)] = "title"
        futures_map[executor.submit(generate_description, transcript, tags_list)] = "description"
        futures_map[executor.submit(generate_caption,     transcript, tags_list)] = "caption"
        futures_map[executor.submit(generate_hashtags,    transcript, tags_list)] = "hashtags"
        futures_map[executor.submit(_chapters_wrapper, None, transcript)]         = "chapters"

        completed = 0
        n = len(futures_map)
        for future in as_completed(futures_map):
            key = futures_map[future]
            try:
                results[key] = future.result()
                upsert_metadata(video_id, **{key: results[key]})
            except Exception as e:
                results[key] = f"Error: {e}"
            completed += 1
            progress(0.22 + (completed / n) * 0.78,
                     desc=f"✅ {key} complete ({completed}/{n})")
            yield (results["tags"], results["title"], results["description"],
                   results["caption"], results["hashtags"], results["chapters"], tags_list)


def regenerate_all_transcript(video_id, progress=gr.Progress()):
    empty = ("", "", "", "", "", "", [])
    if not video_id:
        yield empty
        return
    transcript = get_transcript(video_id)
    if not transcript:
        yield ("⚠️ No transcript in DB.",) + ("",) * 5 + ([],)
        return
    raw_tags = _extract_raw_tags(transcript)
    yield from generate_all_transcript(video_id, transcript, raw_tags, progress)


# ─── Gradio UI ─────────────────────────────────────────────────────────────────

with gr.Blocks(css=custom_css, title="MetaFuse",
               theme=gr.themes.Soft(
                   primary_hue="purple", secondary_hue="purple",
                   neutral_hue="gray", font=gr.themes.GoogleFont("Inter"))) as app:

    gr.HTML("""
        <div class="main-header">
            <h1>🎬 MetaFuse</h1>
            <p>AI-Powered Video Metadata Generator</p>
        </div>
    """)

    with gr.Tabs():

        # ══════════════════════════════════════════════════════════════════════
        # TAB 1 — Upload Video
        # ══════════════════════════════════════════════════════════════════════
        with gr.TabItem("📹 Upload Video"):

            vid_id               = gr.State(None)
            vid_segments         = gr.State([])
            vid_raw_tags         = gr.State([])
            vid_tags             = gr.State([])
            vid_path             = gr.State("")
            vid_transcript_state = gr.State("")

            # ── Upload + Process ──────────────────────────────────────────────
            with gr.Row():
                with gr.Column(scale=1):
                    video_input = gr.Video(label="Drop your video here",
                                           sources=["upload"],
                                           elem_classes=["upload-area"])
                    process_btn = gr.Button("🚀 Process & Upload",
                                            variant="primary", size="lg",
                                            elem_classes=["primary-btn"])

            status_box_v = gr.Textbox(label="Status", lines=3,
                                      interactive=False,
                                      elem_classes=["status-box"])

            transcript_box_v = gr.Textbox(label="📝 Transcript", lines=6,
                                          interactive=False,
                                          elem_classes=["large-text"])

            # ── Metadata section (hidden until video processed) ───────────────
            with gr.Column(visible=False) as meta_col_v:
                gr.HTML('<div class="section-divider"></div>')

                with gr.Row():
                    gen_all_btn_v   = gr.Button("⚡ Generate All (parallel)",
                                                variant="primary", size="lg",
                                                elem_classes=["primary-btn"])
                    regen_all_btn_v = gr.Button("🔄 Regenerate All from DB",
                                                variant="secondary", size="lg",
                                                elem_classes=["regen-btn"])

                gr.HTML('<div class="section-divider"></div>')

                with gr.Row():
                    with gr.Column(scale=1):
                        tags_btn_v = gr.Button("🏷️ Generate Tags", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        tags_box_v = gr.Textbox(label="Tags", lines=2,
                                                elem_classes=["tags-display"])

                with gr.Row():
                    with gr.Column(scale=1):
                        title_btn_v = gr.Button("🎯 Generate Title", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        title_box_v = gr.Textbox(label="Title", lines=2,
                                                 elem_classes=["large-text"])

                with gr.Row():
                    with gr.Column(scale=1):
                        desc_btn_v = gr.Button("📄 Generate Description", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        desc_box_v = gr.Textbox(label="Description", lines=4,
                                                elem_classes=["large-text"])

                with gr.Row():
                    with gr.Column(scale=1):
                        caption_btn_v = gr.Button("💬 Generate Caption", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        caption_box_v = gr.Textbox(label="Caption", lines=2,
                                                   elem_classes=["large-text"])

                with gr.Row():
                    with gr.Column(scale=1):
                        hashtags_btn_v = gr.Button("#️⃣ Generate Hashtags", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        hashtags_box_v = gr.Textbox(label="Hashtags", lines=2,
                                                    elem_classes=["tags-display"])

                with gr.Row():
                    with gr.Column(scale=1):
                        chapters_btn_v = gr.Button("🎬 Generate Chapters", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        chapters_box_v = gr.Textbox(label="Chapters", lines=8,
                                                    elem_classes=["chapters-display"])

                gr.HTML('<div class="section-divider"></div>')
                gr.Markdown("### 🖼️ Thumbnail  ·  Gemini Vision")
                with gr.Row():
                    with gr.Column(scale=1):
                        thumb_btn_v = gr.Button("🖼️ Generate Thumbnail",
                                                elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        thumb_img_v  = gr.Image(label="Thumbnail", type="filepath")
                        thumb_desc_v = gr.Textbox(label="Gemini Recommendation",
                                                  lines=4,
                                                  elem_classes=["large-text"])

            # ── Button wiring ─────────────────────────────────────────────────

            process_btn.click(
                fn=process_video,
                inputs=[video_input],
                outputs=[status_box_v, transcript_box_v, vid_id, vid_segments,
                         vid_raw_tags, vid_path, meta_col_v],
                show_progress=True,
            ).then(
                fn=lambda t: t,
                inputs=[transcript_box_v],
                outputs=[vid_transcript_state],
            )

            tags_btn_v.click(
                fn=gen_tags,
                inputs=[vid_id, vid_transcript_state, vid_raw_tags],
                outputs=[tags_box_v, vid_tags],
                show_progress=True,
            )
            title_btn_v.click(
                fn=gen_title,
                inputs=[vid_id, vid_transcript_state, vid_tags],
                outputs=[title_box_v],
                show_progress=True,
            )
            desc_btn_v.click(
                fn=gen_description,
                inputs=[vid_id, vid_transcript_state, vid_tags],
                outputs=[desc_box_v],
                show_progress=True,
            )
            caption_btn_v.click(
                fn=gen_caption,
                inputs=[vid_id, vid_transcript_state, vid_tags],
                outputs=[caption_box_v],
                show_progress=True,
            )
            hashtags_btn_v.click(
                fn=gen_hashtags,
                inputs=[vid_id, vid_transcript_state, vid_tags],
                outputs=[hashtags_box_v],
                show_progress=True,
            )
            chapters_btn_v.click(
                fn=gen_chapters,
                inputs=[vid_id, vid_transcript_state, vid_segments],
                outputs=[chapters_box_v],
                show_progress=True,
            )
            thumb_btn_v.click(
                fn=gen_thumbnail,
                inputs=[vid_id, title_box_v, vid_transcript_state, vid_tags],
                outputs=[thumb_img_v, thumb_desc_v],
                show_progress=True,
            )

            _ALL_V = [tags_box_v, title_box_v, desc_box_v, caption_box_v,
                      hashtags_box_v, chapters_box_v,
                      thumb_img_v, thumb_desc_v, vid_tags]

            gen_all_btn_v.click(
                fn=generate_all_video,
                inputs=[vid_id, vid_transcript_state, vid_raw_tags,
                        vid_segments, vid_path],
                outputs=_ALL_V,
                show_progress=True,
            )
            regen_all_btn_v.click(
                fn=regenerate_all_video,
                inputs=[vid_id, vid_segments, vid_path],
                outputs=[transcript_box_v] + _ALL_V,
                show_progress=True,
            )

        # ══════════════════════════════════════════════════════════════════════
        # TAB 2 — Paste Transcript
        # ══════════════════════════════════════════════════════════════════════
        with gr.TabItem("📝 Paste Transcript"):

            t_id       = gr.State(None)
            t_raw_tags = gr.State([])
            t_tags     = gr.State([])

            transcript_input_t = gr.Textbox(
                label="Paste your transcript here",
                placeholder="Paste transcript…",
                lines=8,
                elem_classes=["large-text"],
            )
            process_t_btn = gr.Button("🚀 Process Transcript",
                                      variant="primary", size="lg",
                                      elem_classes=["primary-btn"])
            status_t = gr.Textbox(label="Status", lines=1, interactive=False,
                                  elem_classes=["status-box"])

            with gr.Column(visible=False) as meta_col_t:
                gr.HTML('<div class="section-divider"></div>')

                with gr.Row():
                    gen_all_t_btn   = gr.Button("⚡ Generate All (parallel)",
                                                variant="primary", size="lg",
                                                elem_classes=["primary-btn"])
                    regen_all_t_btn = gr.Button("🔄 Regenerate All from DB",
                                                variant="secondary", size="lg",
                                                elem_classes=["regen-btn"])

                gr.HTML('<div class="section-divider"></div>')

                with gr.Row():
                    with gr.Column(scale=1):
                        tags_btn_t = gr.Button("🏷️ Generate Tags", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        tags_box_t = gr.Textbox(label="Tags", lines=2,
                                                elem_classes=["tags-display"])
                with gr.Row():
                    with gr.Column(scale=1):
                        title_btn_t = gr.Button("🎯 Generate Title", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        title_box_t = gr.Textbox(label="Title", lines=2,
                                                 elem_classes=["large-text"])
                with gr.Row():
                    with gr.Column(scale=1):
                        desc_btn_t = gr.Button("📄 Generate Description", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        desc_box_t = gr.Textbox(label="Description", lines=4,
                                                elem_classes=["large-text"])
                with gr.Row():
                    with gr.Column(scale=1):
                        caption_btn_t = gr.Button("💬 Generate Caption", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        caption_box_t = gr.Textbox(label="Caption", lines=2,
                                                   elem_classes=["large-text"])
                with gr.Row():
                    with gr.Column(scale=1):
                        hashtags_btn_t = gr.Button("#️⃣ Generate Hashtags", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        hashtags_box_t = gr.Textbox(label="Hashtags", lines=2,
                                                    elem_classes=["tags-display"])
                with gr.Row():
                    with gr.Column(scale=1):
                        chapters_btn_t = gr.Button("🎬 Generate Chapters", elem_classes=["gen-btn"])
                    with gr.Column(scale=3):
                        chapters_box_t = gr.Textbox(label="Chapters", lines=8,
                                                    elem_classes=["chapters-display"])

            # Wiring
            process_t_btn.click(
                fn=process_transcript_tab,
                inputs=[transcript_input_t],
                outputs=[status_t, t_id, t_raw_tags, meta_col_t],
                show_progress=True,
            )
            tags_btn_t.click(
                fn=gen_tags,
                inputs=[t_id, transcript_input_t, t_raw_tags],
                outputs=[tags_box_t, t_tags],
                show_progress=True,
            )
            title_btn_t.click(
                fn=gen_title,
                inputs=[t_id, transcript_input_t, t_tags],
                outputs=[title_box_t],
                show_progress=True,
            )
            desc_btn_t.click(
                fn=gen_description,
                inputs=[t_id, transcript_input_t, t_tags],
                outputs=[desc_box_t],
                show_progress=True,
            )
            caption_btn_t.click(
                fn=gen_caption,
                inputs=[t_id, transcript_input_t, t_tags],
                outputs=[caption_box_t],
                show_progress=True,
            )
            hashtags_btn_t.click(
                fn=gen_hashtags,
                inputs=[t_id, transcript_input_t, t_tags],
                outputs=[hashtags_box_t],
                show_progress=True,
            )
            chapters_btn_t.click(
                fn=gen_chapters,
                inputs=[t_id, transcript_input_t, gr.State([])],
                outputs=[chapters_box_t],
                show_progress=True,
            )

            _ALL_T = [tags_box_t, title_box_t, desc_box_t, caption_box_t,
                      hashtags_box_t, chapters_box_t, t_tags]

            gen_all_t_btn.click(
                fn=generate_all_transcript,
                inputs=[t_id, transcript_input_t, t_raw_tags],
                outputs=_ALL_T,
                show_progress=True,
            )
            regen_all_t_btn.click(
                fn=regenerate_all_transcript,
                inputs=[t_id],
                outputs=_ALL_T,
                show_progress=True,
            )

    gr.HTML("""
        <div style="text-align:center;color:#6B7280;font-size:.95rem;
                    padding:1.2rem;margin-top:1rem;">
            💡 <strong>Tip:</strong> Each button generates &amp; saves that field independently.
            <em>Generate All</em> runs every pipeline in parallel.
            <em>Regenerate All from DB</em> re-runs using the stored transcript.
        </div>
    """)


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=8000,
        share=False,
        show_error=True,
    )

