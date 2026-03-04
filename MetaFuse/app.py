import gradio as gr
from pathlib import Path

from utils.config_loader import load_config
from pipelines.audio_pipeline import split_audio
from pipelines.transcript_pipeline import transcribe
from pipelines.keyword_pipeline import extract_keywords
from pipelines.tag_pipeline import TagRanker
from pipelines.llm_pipeline import generate_metadata, refine_tags_with_llm, generate_chapters

cfg = load_config()

# Initialize tag ranker (cached)
tag_ranker = None

def get_tag_ranker():
    global tag_ranker
    if tag_ranker is None:
        tag_ranker = TagRanker()
    return tag_ranker

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
"""


# ─── Helper: run tags → metadata pipeline ────────────────────────────────────
def _run_tags_and_metadata(transcript_text, progress, step_offset=0, total_steps=4):
    """Shared logic: keyword extraction → tag ranking → LLM refinement → metadata."""
    ranker = get_tag_ranker()
    max_tags = cfg.get("tags", {}).get("max_tags", 10)

    progress((step_offset + 0) / total_steps, desc=f"Step {step_offset+1}/{total_steps}: Extracting keywords...")
    keywords = extract_keywords(transcript_text, top_n=50)

    progress((step_offset + 1) / total_steps, desc=f"Step {step_offset+2}/{total_steps}: Ranking tags...")
    raw_tags = ranker.rank(transcript_text, keywords)

    progress((step_offset + 2) / total_steps, desc=f"Step {step_offset+3}/{total_steps}: Optimizing tags with AI...")
    refined_tags = refine_tags_with_llm(transcript_text, raw_tags, max_tags=max_tags)

    progress((step_offset + 3) / total_steps, desc=f"Step {step_offset+4}/{total_steps}: Generating metadata...")
    metadata = generate_metadata(transcript_text, refined_tags)

    title = metadata.get("title", "N/A")
    description = metadata.get("description", "N/A")
    caption = metadata.get("caption", "N/A")
    hashtags = metadata.get("hashtags", "")
    tags_str = ", ".join(refined_tags) if refined_tags else "N/A"
    return title, description, caption, hashtags, tags_str


# ─── Video tab functions ──────────────────────────────────────────────────────
def process_video(video_file, progress=gr.Progress()):
    """Full pipeline: audio split → transcription → tags → metadata."""
    if video_file is None:
        empty = ("Please upload a video file.", "", "", "", "", "", "", [])
        return empty

    try:
        video_path = Path(video_file)

        progress(0.05, desc="Step 1/5: Splitting audio...")
        chunks = split_audio(video_path)

        progress(0.15, desc="Step 2/5: Transcribing with Whisper...")
        transcript, timed_segments = transcribe(chunks)

        if not transcript or len(transcript.strip()) == 0:
            return "Failed to generate transcript. Please check the video file.", "", "", "", "", "", "", []

        title, description, caption, hashtags, tags_str = _run_tags_and_metadata(
            transcript, progress, step_offset=2, total_steps=5
        )
        progress(1.0, desc="✅ Complete!")

        # Return outputs + hidden state values (transcript text + timed segments)
        return transcript, title, description, caption, hashtags, tags_str, transcript, timed_segments

    except Exception as e:
        return f"Error: {str(e)}", "", "", "", "", "", "", []


def regenerate_video(transcript_state, segments_state, progress=gr.Progress()):
    """Re-run tags + metadata using the already-stored transcript (no re-transcription)."""
    if not transcript_state or not transcript_state.strip():
        return "⚠️ No transcript available. Please run Generate Metadata first.", "", "", "", ""

    try:
        title, description, caption, hashtags, tags_str = _run_tags_and_metadata(
            transcript_state, progress, step_offset=0, total_steps=4
        )
        progress(1.0, desc="✅ Regenerated!")
        return title, description, caption, hashtags, tags_str
    except Exception as e:
        return f"Error: {str(e)}", "", "", "", ""


def generate_chapters_video(segments_state, progress=gr.Progress()):
    """Generate chapters using real Whisper timestamps from stored state."""
    progress(0.2, desc="Generating chapters with AI...")
    if segments_state:
        result = generate_chapters(timed_segments=segments_state)
    else:
        result = "⚠️ No timed segments found. Please run Generate Metadata first."
    progress(1.0, desc="✅ Chapters ready!")
    return result


# ─── Transcript tab functions ─────────────────────────────────────────────────
def process_transcript_only(transcript_text, progress=gr.Progress()):
    """Run tags + metadata from a plain-text transcript."""
    if not transcript_text or len(transcript_text.strip()) == 0:
        return "Please enter a transcript.", "", "", "", ""

    try:
        title, description, caption, hashtags, tags_str = _run_tags_and_metadata(
            transcript_text, progress, step_offset=0, total_steps=4
        )
        progress(1.0, desc="✅ Complete!")
        return title, description, caption, hashtags, tags_str
    except Exception as e:
        return f"Error: {str(e)}", "", "", "", ""


def generate_chapters_text(transcript_text, progress=gr.Progress()):
    """Generate chapters with estimated timestamps from plain transcript text."""
    if not transcript_text or not transcript_text.strip():
        return "⚠️ Please enter a transcript first, then generate metadata before generating chapters."
    progress(0.2, desc="Estimating chapters with AI...")
    result = generate_chapters(transcript=transcript_text)
    progress(1.0, desc="✅ Chapters ready!")
    return result


# ─── Gradio UI ────────────────────────────────────────────────────────────────
with gr.Blocks(css=custom_css, title="MetaFuse - AI Video Metadata Generator",
               theme=gr.themes.Soft(
                   primary_hue="purple",
                   secondary_hue="purple",
                   neutral_hue="gray",
                   font=gr.themes.GoogleFont("Inter")
               )) as app:

    # Header
    gr.HTML("""
        <div class="main-header">
            <h1>🎬 MetaFuse</h1>
            <p>AI-Powered Video Metadata Generator</p>
        </div>
    """)

    with gr.Tabs() as tabs:

        # ── Tab 1: Video Upload ───────────────────────────────────────────────
        with gr.TabItem("📹 Upload Video", id=1):
            gr.Markdown("### Upload your video to generate optimized metadata",
                        elem_classes=["section-header"])

            # Hidden states: transcript text and Whisper timed segments
            transcript_state_v = gr.State("")
            segments_state_v   = gr.State([])

            with gr.Row():
                with gr.Column(scale=1):
                    video_input = gr.Video(
                        label="Drop your video here",
                        sources=["upload"],
                        elem_classes=["upload-area"]
                    )
                    with gr.Row():
                        process_video_btn = gr.Button(
                            "🚀 Generate Metadata",
                            variant="primary",
                            size="lg",
                            elem_classes=["primary-btn"]
                        )
                        regenerate_video_btn = gr.Button(
                            "🔄 Regenerate",
                            variant="secondary",
                            size="lg",
                            elem_classes=["secondary-btn"]
                        )

            gr.Markdown("---")
            gr.Markdown("## 📊 Results", elem_classes=["section-header"])

            with gr.Row():
                transcript_output = gr.Textbox(
                    label="📝 Transcript",
                    lines=6,
                    elem_classes=["large-text"]
                )

            with gr.Row():
                with gr.Column():
                    title_output_v = gr.Textbox(
                        label="🎯 Title",
                        lines=2,
                        elem_classes=["large-text"]
                    )
                with gr.Column():
                    caption_output_v = gr.Textbox(
                        label="💬 Caption",
                        lines=2,
                        elem_classes=["large-text"]
                    )

            with gr.Row():
                hashtags_output_v = gr.Textbox(
                    label="#️⃣ Hashtags",
                    lines=2,
                    elem_classes=["tags-display"]
                )

            with gr.Row():
                description_output_v = gr.Textbox(
                    label="📄 Description",
                    lines=4,
                    elem_classes=["large-text"]
                )

            with gr.Row():
                tags_output_v = gr.Textbox(
                    label="🏷️ Tags",
                    lines=2,
                    elem_classes=["tags-display"]
                )

            # ── Chapter section (optional) ────────────────────────────────────
            gr.Markdown("---")
            gr.HTML("""
                <div style="background:#F0F9FF; border:2px solid #BAE6FD; border-radius:12px;
                            padding:1rem 1.5rem; margin:0.5rem 0;">
                    <strong style="color:#0284C7; font-size:1.1rem;">🎬 Chapter Generation (Optional)</strong><br>
                    <span style="color:#374151; font-size:0.95rem;">
                       
                        Click the button below after metadata has been generated.
                    </span>
                </div>
            """)
            with gr.Row():
                generate_chapters_v_btn = gr.Button(
                    "📑 Generate Chapters",
                    variant="secondary",
                    size="lg",
                    elem_classes=["chapter-btn"]
                )
            with gr.Row():
                chapters_output_v = gr.Textbox(
                    label="🎬 Video Chapters",
                    lines=10,
                    placeholder="Chapters will appear here after clicking Generate Chapters...",
                    elem_classes=["chapters-display"]
                )

            # ── Button wiring ─────────────────────────────────────────────────
            process_video_btn.click(
                fn=process_video,
                inputs=[video_input],
                outputs=[
                    transcript_output,
                    title_output_v, description_output_v, caption_output_v, hashtags_output_v, tags_output_v,
                    transcript_state_v, segments_state_v
                ],
                show_progress=True
            )

            regenerate_video_btn.click(
                fn=regenerate_video,
                inputs=[transcript_state_v, segments_state_v],
                outputs=[title_output_v, description_output_v, caption_output_v, hashtags_output_v, tags_output_v],
                show_progress=True
            )

            generate_chapters_v_btn.click(
                fn=generate_chapters_video,
                inputs=[segments_state_v],
                outputs=[chapters_output_v],
                show_progress=True
            )

        # ── Tab 2: Paste Transcript ───────────────────────────────────────────
        with gr.TabItem("📝 Paste Transcript", id=2):
            gr.Markdown("### Already have a transcript? Paste it below for faster processing",
                        elem_classes=["section-header"])

            with gr.Row():
                transcript_input = gr.Textbox(
                    label="Your Transcript",
                    placeholder="Paste your video transcript here...",
                    lines=8,
                    elem_classes=["large-text"]
                )

            with gr.Row():
                process_transcript_btn = gr.Button(
                    "🚀 Generate Metadata",
                    variant="primary",
                    size="lg",
                    elem_classes=["primary-btn"]
                )
                regenerate_transcript_btn = gr.Button(
                    "🔄 Regenerate",
                    variant="secondary",
                    size="lg",
                    elem_classes=["secondary-btn"]
                )

            gr.Markdown("---")
            gr.Markdown("## 📊 Results", elem_classes=["section-header"])

            with gr.Row():
                with gr.Column():
                    title_output_t = gr.Textbox(
                        label="🎯 Title",
                        lines=2,
                        elem_classes=["large-text"]
                    )
                with gr.Column():
                    caption_output_t = gr.Textbox(
                        label="💬 Caption",
                        lines=2,
                        elem_classes=["large-text"]
                    )

            with gr.Row():
                hashtags_output_t = gr.Textbox(
                    label="#️⃣ Hashtags",
                    lines=2,
                    elem_classes=["tags-display"]
                )

            with gr.Row():
                description_output_t = gr.Textbox(
                    label="📄 Description",
                    lines=4,
                    elem_classes=["large-text"]
                )

            with gr.Row():
                tags_output_t = gr.Textbox(
                    label="🏷️ Tags",
                    lines=2,
                    elem_classes=["tags-display"]
                )

            # ── Chapter section (optional) ────────────────────────────────────
            gr.Markdown("---")
            gr.HTML("""
                <div style="background:#F0F9FF; border:2px solid #BAE6FD; border-radius:12px;
                            padding:1rem 1.5rem; margin:0.5rem 0;">
                    <strong style="color:#0284C7; font-size:1.1rem;">🎬 Chapter Generation (Optional)</strong><br>
                    <span style="color:#374151; font-size:0.95rem;">
                        Generate estimated YouTube chapter markers from the transcript text.
                        Timestamps are AI-estimated based on content structure and pacing.
                    </span>
                </div>
            """)
            with gr.Row():
                generate_chapters_t_btn = gr.Button(
                    "📑 Generate Chapters",
                    variant="secondary",
                    size="lg",
                    elem_classes=["chapter-btn"]
                )
            with gr.Row():
                chapters_output_t = gr.Textbox(
                    label="🎬 Video Chapters (Estimated)",
                    lines=10,
                    placeholder="Chapters will appear here after clicking Generate Chapters...",
                    elem_classes=["chapters-display"]
                )

            # ── Button wiring ─────────────────────────────────────────────────
            process_transcript_btn.click(
                fn=process_transcript_only,
                inputs=[transcript_input],
                outputs=[title_output_t, description_output_t, caption_output_t, hashtags_output_t, tags_output_t],
                show_progress=True
            )

            regenerate_transcript_btn.click(
                fn=process_transcript_only,
                inputs=[transcript_input],
                outputs=[title_output_t, description_output_t, caption_output_t, hashtags_output_t, tags_output_t],
                show_progress=True
            )

            generate_chapters_t_btn.click(
                fn=generate_chapters_text,
                inputs=[transcript_input],
                outputs=[chapters_output_t],
                show_progress=True
            )

    # Footer
    gr.HTML("""
        <div class="footer-text">
            <p>💡 <strong>Tip:</strong> Use <em>Regenerate</em> to get fresh metadata without re-transcribing.
               Use <em>Generate Chapters</em> to add YouTube chapter markers anytime.</p>
        </div>
    """)


if __name__ == "__main__":
    app.launch(
        server_name="127.0.0.1",
        server_port=8000,
        share=False,
        show_error=True
    )

