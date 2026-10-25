import re
from io import BytesIO
from xml.sax.saxutils import escape

import streamlit as st
import yt_dlp
from app import buil_youtube_agent
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Framewise | AI YouTube Video Analyzer",
    page_icon="📹",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Custom UI styling
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --fw-red: #e33b35;
        --fw-red-dark: #c92e29;
        --fw-ink: #20232b;
        --fw-muted: #777984;
    }
    .stApp {
        background: linear-gradient(180deg, rgba(227,59,53,.035), transparent 360px);
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(130,130,145,.18);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
        letter-spacing: -.5px;
    }
    .brand-row {
        display:flex; align-items:center; gap:12px; margin: 4px 0 22px;
    }
    .brand-mark {
        display:flex; align-items:center; justify-content:center;
        width:46px; height:46px; border-radius:14px;
        background:var(--fw-red); color:#fff; font-size:24px;
        box-shadow:0 8px 22px rgba(227,59,53,.22);
    }
    .brand-name { font-size:24px; font-weight:850; line-height:1.05; }
    .brand-caption { font-size:10px; font-weight:800; letter-spacing:2px; opacity:.58; margin-top:5px; }
    .hero {
        padding: 34px 34px 30px;
        border-radius: 22px;
        border: 1px solid rgba(130,130,145,.18);
        background: linear-gradient(125deg, rgba(227,59,53,.11), rgba(130,130,145,.035));
        margin-bottom: 26px;
    }
    .eyebrow {
        display:inline-block; padding:7px 11px; border-radius:999px;
        background:rgba(227,59,53,.11); color:var(--fw-red);
        font-size:10px; font-weight:850; letter-spacing:1.5px;
    }
    .hero h1 { font-size: clamp(2rem, 4vw, 3.6rem); line-height:1.04; letter-spacing:-2px; margin:18px 0 14px; }
    .hero h1 span { color:var(--fw-red); }
    .hero p { font-size:1.02rem; line-height:1.75; max-width:780px; opacity:.76; margin:0; }
    .section-kicker { font-size:10px; font-weight:850; letter-spacing:1.7px; color:var(--fw-red); }
    .feature-card {
        padding:22px; border:1px solid rgba(130,130,145,.22);
        border-radius:16px; height:100%;
        background:rgba(130,130,145,.035);
    }
    .feature-icon { font-size:25px; margin-bottom:12px; }
    .feature-card h3 { font-size:1.05rem; margin:0 0 8px; }
    .feature-card p { font-size:.9rem; line-height:1.7; opacity:.72; margin:0; }
    .step-card {
        border:1px solid rgba(130,130,145,.22); border-radius:15px;
        padding:20px; height:100%; background:rgba(130,130,145,.035);
    }
    .step-number {
        width:34px; height:34px; border-radius:10px; background:var(--fw-red);
        color:#fff; display:flex; align-items:center; justify-content:center;
        font-size:12px; font-weight:850; margin-bottom:14px;
    }
    .info-card {
        border:1px solid rgba(130,130,145,.22); border-radius:16px;
        padding:20px; background:rgba(130,130,145,.035); margin-bottom:14px;
    }
    .status-chip {
        display:inline-block; padding:7px 10px; border-radius:999px;
        font-size:11px; font-weight:800; background:rgba(22,163,106,.12);
        color:#16a36a;
    }
    div.stButton > button[kind="primary"] {
        background:var(--fw-red); border-color:var(--fw-red); color:#fff;
        border-radius:10px; font-weight:750;
    }
    div.stButton > button[kind="primary"]:hover {
        background:var(--fw-red-dark); border-color:var(--fw-red-dark); color:#fff;
    }
    div[data-testid="stDownloadButton"] button {
        border-radius:10px; font-weight:700;
    }
    @media (max-width: 700px) {
        .hero { padding:24px; }
        .hero h1 { letter-spacing:-1px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Agent cache
# ---------------------------------------------------------
@st.cache_resource
def get_agent():
    return buil_youtube_agent()


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
YOUTUBE_PATTERN = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$",
    re.IGNORECASE,
)


def is_valid_youtube_url(url: str) -> bool:
    """Validate a YouTube URL and require a recognizable video ID."""
    url = (url or "").strip()
    if not YOUTUBE_PATTERN.match(url):
        return False

    # Support standard watch links, youtu.be links, Shorts, and embed URLs.
    video_id_pattern = re.compile(
        r"(?:youtube\.com/(?:watch\?.*v=|shorts/|embed/)|youtu\.be/)([A-Za-z0-9_-]{6,})",
        re.IGNORECASE,
    )
    return bool(video_id_pattern.search(url))


def get_video_info(url: str):
    ydl_opts = {"quiet": True, "skip_download": True, "no_warnings": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title") or "Unknown title",
            "channel": info.get("uploader") or "Unknown channel",
            "duration": info.get("duration"),
            "views": info.get("view_count"),
            "upload_date": info.get("upload_date"),
            "thumbnail": info.get("thumbnail"),
        }
    except Exception:
        return None


def format_duration(seconds):
    if seconds is None:
        return "Unknown"
    minutes, remaining_seconds = divmod(int(seconds), 60)
    return f"{minutes} min {remaining_seconds} sec"


def build_prompt(video_url: str, analysis_type: str) -> str:
    instructions = {
        "Summary": """
            Provide a concise summary, the main topics, and the final conclusion.
        """,
        "Detailed Analysis": """
            Provide a complete explanation, timestamps only if available,
            important concepts, examples, and a final conclusion.
        """,
        "Key Takeaways": """
            Extract the top 10 key takeaways, important insights, and actionable points.
        """,
        "Study Notes": """
            Create clean study notes with headings, bullet points, and important facts.
        """,
        "Quiz": """
            Create 10 multiple-choice questions, identify the correct answer,
            and provide a short explanation for each answer.
        """,
    }
    return f"""
    Analyze the following YouTube video using the available video/transcript tools.
    Do not invent transcript content or timestamps. If the video's content cannot
    be accessed, clearly state that limitation instead of guessing.

    URL:
    {video_url}

    Analysis mode: {analysis_type}

    {instructions[analysis_type]}
    """


def create_pdf(content: str) -> bytes:
    """Create a PDF safely from AI-generated text."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
    )
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "FramewiseBody",
        parent=styles["BodyText"],
        leading=15,
        spaceAfter=7,
    )
    story = [
        Paragraph("AI YouTube Video Analysis Report", styles["Title"]),
        Spacer(1, 14),
    ]

    for raw_line in (content or "").splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue

        # Escape XML characters before adding safe line breaks.
        safe_line = escape(line)
        safe_line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe_line)
        safe_line = re.sub(r"^#{1,6}\s+", "", safe_line)
        if safe_line.startswith(("- ", "* ")):
            safe_line = "• " + safe_line[2:]
        story.append(Paragraph(safe_line, body_style))

    doc.build(story)
    return buffer.getvalue()


ANALYSIS_TYPES = [
    "Summary",
    "Detailed Analysis",
    "Key Takeaways",
    "Study Notes",
    "Quiz",
]


# ---------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
          <div class="brand-mark">▶</div>
          <div>
            <div class="brand-name">Framewise</div>
            <div class="brand-caption">VIDEO INTELLIGENCE</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    page = st.radio(
        "NAVIGATION",
        ["About", "Check Video", "How It Works"],
        index=0,
        label_visibility="visible",
    )
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.write("Turn YouTube videos into summaries, study notes, takeaways, and quizzes.")
    st.caption("Built with Streamlit · Agno · Groq · yt-dlp · ReportLab")


# ---------------------------------------------------------
# Page 1: About
# ---------------------------------------------------------
if page == "About":
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">✦ AI-POWERED VIDEO NOTES</div>
          <h1>Watch less twice.<br><span>Understand more.</span></h1>
          <p>Turn YouTube videos into useful summaries, detailed explanations, key takeaways,
          study notes, and quizzes — all from one clean workspace.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([1.15, 0.85], gap="large")
    with col1:
        st.markdown("### One link. Five useful outcomes.")
        st.write(
            "Choose the type of understanding you need, from a quick overview "
            "to a self-check quiz."
        )
        f1, f2 = st.columns(2)
        with f1:
            st.markdown(
                '<div class="feature-card"><div class="feature-icon">▤</div>'
                "<h3>Quick summaries</h3><p>Get the central idea, main topics, "
                "and conclusion in a concise report.</p></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="feature-card"><div class="feature-icon">✎</div>'
                "<h3>Study-ready notes</h3><p>Organize the content into headings, "
                "key facts, and clear bullet points.</p></div>",
                unsafe_allow_html=True,
            )
        with f2:
            st.markdown(
                '<div class="feature-card"><div class="feature-icon">⌕</div>'
                "<h3>Detailed analysis</h3><p>Explore concepts, examples, and "
                "timestamps when available.</p></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="feature-card"><div class="feature-icon">☷</div>'
                "<h3>Quiz mode</h3><p>Create multiple-choice questions to check "
                "your understanding.</p></div>",
                unsafe_allow_html=True,
            )
    with col2:
        st.markdown(
            """
            <div class="info-card">
              <div class="section-kicker">PROJECT SNAPSHOT</div>
              <h3>Built around your Python agent</h3>
              <p>Framewise keeps the existing Agno/Groq workflow and yt-dlp
              metadata lookup, while giving the app a clearer multi-page interface.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("#### Supported analysis modes")
        for mode, detail in [
            ("Summary", "A concise overview and conclusion"),
            ("Detailed Analysis", "Concepts, examples, and available timestamps"),
            ("Key Takeaways", "Top insights and actionable points"),
            ("Study Notes", "Headings, bullet points, and important facts"),
            ("Quiz", "10 multiple-choice questions with answers"),
        ]:
            st.write(f"**{mode}** — {detail}")
    st.markdown("---")
    st.markdown("### Technology stack")
    tech_cols = st.columns(5)
    for col, tech in zip(tech_cols, ["Streamlit", "Agno Agent", "Groq", "yt-dlp", "ReportLab"]):
        with col:
            st.markdown(f'<div class="feature-card" style="text-align:center;padding:14px">{tech}</div>', unsafe_allow_html=True)
    st.info("Use **Check Video** in the sidebar to analyze a YouTube video.")


# ---------------------------------------------------------
# Page 2: Check Video
# ---------------------------------------------------------
elif page == "Check Video":
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">ANALYZER WORKSPACE</div>
          <h1>Make a video easier to use.</h1>
          <p>Paste a YouTube URL, select an analysis mode, and generate a report
          using your configured Agno agent and Groq model.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.25, 0.75], gap="large")
    with left:
        st.markdown("### 01 / Video input")
        video_url = st.text_input(
            "YouTube video URL",
            placeholder="https://www.youtube.com/watch?v=...",
            key="video_url",
        )
        analysis_type = st.selectbox(
            "02 / Choose an analysis mode",
            ANALYSIS_TYPES,
            key="analysis_type",
        )
        analyze_clicked = st.button(
            "🚀 Analyze Video",
            type="primary",
            use_container_width=True,
        )
        st.caption("Analysis time depends on video length, transcript availability, and model response time.")

    with right:
        st.markdown("### What happens next?")
        st.markdown(
            """
            <div class="info-card"><b>01 · Validate</b><br>Check the YouTube URL format.</div>
            <div class="info-card"><b>02 · Retrieve metadata</b><br>Attempt to fetch title, channel, duration, and thumbnail.</div>
            <div class="info-card"><b>03 · Analyze with AI</b><br>Send the selected prompt to your configured Agno agent.</div>
            <div class="info-card"><b>04 · Export</b><br>Review the response and download TXT or PDF.</div>
            """,
            unsafe_allow_html=True,
        )

    if analyze_clicked:
        if not video_url.strip():
            st.warning("Please enter a YouTube video URL.")
        elif not is_valid_youtube_url(video_url):
            st.error("Invalid YouTube URL. Use a valid youtube.com or youtu.be video link.")
        else:
            st.success("YouTube URL format looks valid.")
            with st.spinner("Fetching video information..."):
                video_info = get_video_info(video_url.strip())

            if video_info:
                st.markdown("### 🎬 Video information")
                info_col, thumb_col = st.columns([1.4, 1])
                with info_col:
                    st.write(f"**Title:** {video_info['title']}")
                    st.write(f"**Channel:** {video_info['channel']}")
                    st.write(f"**Duration:** {format_duration(video_info['duration'])}")
                    views = video_info.get("views")
                    st.write(f"**Views:** {f'{views:,}' if views is not None else 'Not available'}")
                    upload = video_info.get("upload_date")
                    if upload and len(upload) == 8:
                        upload = f"{upload[:4]}-{upload[4:6]}-{upload[6:]}"
                    st.write(f"**Upload date:** {upload or 'Not available'}")
                with thumb_col:
                    if video_info.get("thumbnail"):
                        st.image(video_info["thumbnail"], use_container_width=True)
            else:
                st.warning(
                    "Video metadata could not be retrieved. The AI agent will still be "
                    "called, but it may fail if the video or transcript is inaccessible."
                )

            progress = st.progress(0, text="Preparing analysis...")
            try:
                progress.progress(20, text="Preparing analysis prompt...")
                prompt = build_prompt(video_url.strip(), analysis_type)

                progress.progress(45, text="Initializing AI agent...")
                agent = get_agent()

                progress.progress(70, text="AI is analyzing the video...")
                response = agent.run(prompt)
                content = getattr(response, "content", None)
                if not content:
                    content = str(response)

                progress.progress(100, text="Analysis complete")
                st.success("Analysis completed.")

                st.markdown("---")
                st.markdown("### 📄 Analysis report")
                st.markdown(content)

                pdf_bytes = create_pdf(content)
                safe_mode = analysis_type.lower().replace(" ", "_")
                txt_name = f"youtube_{safe_mode}_analysis.txt"
                pdf_name = f"youtube_{safe_mode}_analysis.pdf"

                download_col1, download_col2 = st.columns(2)
                with download_col1:
                    st.download_button(
                        "📥 Download report (.txt)",
                        data=content,
                        file_name=txt_name,
                        mime="text/plain",
                        use_container_width=True,
                    )
                with download_col2:
                    st.download_button(
                        "📄 Download report (PDF)",
                        data=pdf_bytes,
                        file_name=pdf_name,
                        mime="application/pdf",
                        use_container_width=True,
                    )
            except Exception as exc:
                progress.empty()
                st.error(
                    "An error occurred while analyzing the video. Check your API key, "
                    "agent configuration, dependencies, and video/transcript access."
                )
                st.exception(exc)


# ---------------------------------------------------------
# Page 3: How It Works
# ---------------------------------------------------------
elif page == "How It Works":
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">HOW IT WORKS</div>
          <h1>From YouTube link to useful insights.</h1>
          <p>Framewise follows a simple pipeline: validate the input, retrieve available
          video metadata, request AI analysis, and prepare a report for export.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown(
            '<div class="step-card"><div class="step-number">01</div>'
            "<h3>Check the video link</h3><p>Paste a YouTube URL. The app validates "
            "its format and attempts to retrieve available metadata using yt-dlp.</p></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="step-card"><div class="step-number">02</div>'
            "<h3>Choose an analysis mode</h3><p>Select Summary, Detailed Analysis, "
            "Key Takeaways, Study Notes, or Quiz. The prompt is sent to the Agno agent.</p></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="step-card"><div class="step-number">03</div>'
            "<h3>Review and download</h3><p>Read the model response and export it as "
            "a TXT file or a PDF report generated with ReportLab.</p></div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")
    st.markdown("### Architecture")
    st.code(
        "YouTube URL\n"
        "    ↓\n"
        "URL validation + yt-dlp metadata lookup\n"
        "    ↓\n"
        "Analysis prompt based on selected mode\n"
        "    ↓\n"
        "Agno agent + configured Groq model\n"
        "    ↓\n"
        "AI report → Streamlit display → TXT / PDF download",
        language="text",
    )
    st.warning(
        "The quality of the analysis depends on whether the configured agent can access "
        "the video's transcript/content. If content is unavailable, the model should say so "
        "rather than inventing details."
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Built with ❤️ using Streamlit + Agno + Groq · Framewise AI YouTube Video Analyzer")
