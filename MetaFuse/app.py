import gradio as gr
from pathlib import Path
import json
import tempfile
import shutil

from utils.config_loader import load_config
from pipelines.audio_pipeline import split_audio
from pipelines.transcript_pipeline import transcribe
from pipelines.keyword_pipeline import extract_keywords
from pipelines.tag_pipeline import TagRanker
from pipelines.llm_pipeline import generate_metadata, refine_tags_with_llm

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

/* Hide raw tags completely */
.hide-element {
    display: none !important;
}
"""


def process_video(video_file, progress=gr.Progress()):
    """Process a video file and generate metadata."""
    if video_file is None:
        return "Please upload a video file.", "", "", "", ""
    
    try:
        video_path = Path(video_file)
        
        # Step 1: Transcribe
        progress(0.1, desc="Step 1/5: Extracting audio and transcribing...")
        chunks = split_audio(video_path)
        transcript = transcribe(chunks)
        
        if not transcript or len(transcript.strip()) == 0:
            return "Failed to generate transcript. Please check the video file.", "", "", "", ""
        
        # Step 2: Extract keywords
        progress(0.4, desc="Step 2/5: Extracting keywords...")
        keywords = extract_keywords(transcript, top_n=50)
        
        # Step 3: Rank tags
        progress(0.6, desc="Step 3/5: Ranking tags...")
        ranker = get_tag_ranker()
        raw_tags = ranker.rank(transcript, keywords)
        
        # Step 4: Refine tags with LLM (backend only, not shown to user)
        progress(0.75, desc="Step 4/5: Optimizing tags...")
        max_tags = cfg.get("tags", {}).get("max_tags", 10)
        refined_tags = refine_tags_with_llm(transcript, raw_tags, max_tags=max_tags)
        
        # Step 5: Generate metadata
        progress(0.9, desc="Step 5/5: Generating metadata...")
        metadata = generate_metadata(transcript, refined_tags)
        
        progress(1.0, desc="Complete!")
        
        title = metadata.get("title", "N/A")
        description = metadata.get("description", "N/A")
        caption = metadata.get("caption", "N/A")
        tags_str = ", ".join(refined_tags) if refined_tags else "N/A"
        
        return transcript, title, description, caption, tags_str
        
    except Exception as e:
        return f"Error: {str(e)}", "", "", "", ""


def process_transcript_only(transcript_text, progress=gr.Progress()):
    """Process an existing transcript to generate metadata."""
    if not transcript_text or len(transcript_text.strip()) == 0:
        return "Please enter a transcript.", "", "", ""
    
    try:
        # Step 1: Extract keywords
        progress(0.2, desc="Step 1/4: Extracting keywords...")
        keywords = extract_keywords(transcript_text, top_n=50)
        
        # Step 2: Rank tags
        progress(0.4, desc="Step 2/4: Ranking tags...")
        ranker = get_tag_ranker()
        raw_tags = ranker.rank(transcript_text, keywords)
        
        # Step 3: Refine tags with LLM (backend only)
        progress(0.6, desc="Step 3/4: Optimizing tags...")
        max_tags = cfg.get("tags", {}).get("max_tags", 10)
        refined_tags = refine_tags_with_llm(transcript_text, raw_tags, max_tags=max_tags)
        
        # Step 4: Generate metadata
        progress(0.85, desc="Step 4/4: Generating metadata...")
        metadata = generate_metadata(transcript_text, refined_tags)
        
        progress(1.0, desc="Complete!")
        
        title = metadata.get("title", "N/A")
        description = metadata.get("description", "N/A")
        caption = metadata.get("caption", "N/A")
        tags_str = ", ".join(refined_tags) if refined_tags else "N/A"
        
        return title, description, caption, tags_str
        
    except Exception as e:
        return f"Error: {str(e)}", "", "", ""


# Create Gradio interface with custom theme
with gr.Blocks(title="MetaFuse - AI Video Metadata Generator") as app:
    
    # Header
    gr.HTML("""
        <div class="main-header">
            <h1>🎬 MetaFuse</h1>
            <p>AI-Powered Video Metadata Generator</p>
        </div>
    """)
    
    with gr.Tabs() as tabs:
        # Tab 1: Video Upload
        with gr.TabItem("📹 Upload Video", id=1):
            gr.Markdown("### Upload your video to generate optimized metadata", elem_classes=["section-header"])
            
            with gr.Row():
                with gr.Column(scale=1):
                    video_input = gr.Video(
                        label="Drop your video here",
                        sources=["upload"],
                        elem_classes=["upload-area"]
                    )
                    process_video_btn = gr.Button(
                        "🚀 Generate Metadata", 
                        variant="primary", 
                        size="lg",
                        elem_classes=["primary-btn"]
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
            
            process_video_btn.click(
                fn=process_video,
                inputs=[video_input],
                outputs=[transcript_output, title_output_v, description_output_v, caption_output_v, tags_output_v],
                show_progress=True
            )
        
        # Tab 2: Transcript Input
        with gr.TabItem("📝 Paste Transcript", id=2):
            gr.Markdown("### Already have a transcript? Paste it below for faster processing", elem_classes=["section-header"])
            
            with gr.Row():
                transcript_input = gr.Textbox(
                    label="Your Transcript",
                    placeholder="Paste your video transcript here...",
                    lines=8,
                    elem_classes=["large-text"]
                )
            
            process_transcript_btn = gr.Button(
                "🚀 Generate Metadata", 
                variant="primary", 
                size="lg",
                elem_classes=["primary-btn"]
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
            
            process_transcript_btn.click(
                fn=process_transcript_only,
                inputs=[transcript_input],
                outputs=[title_output_t, description_output_t, caption_output_t, tags_output_t],
                show_progress=True
            )
    
    # Footer
    gr.HTML("""
        <div class="footer-text">
            <p>💡 <strong>Tip:</strong> Video processing may take a few minutes depending on length. Use the transcript tab for faster results.</p>
        </div>
    """)


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        css=custom_css,
        theme=gr.themes.Soft(
            primary_hue="purple",
            secondary_hue="purple",
            neutral_hue="gray",
            font=gr.themes.GoogleFont("Inter")
        )
    )
