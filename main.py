import re
import yt_dlp
import streamlit as st
from app import buil_youtube_agent
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# ----------------------------
# Page Configuration
# ----------------------------
st.set_page_config(
    page_title="AI YouTube Video Analyzer",
    page_icon="📹",
    layout="centered"
)

# ----------------------------
# Title
# ----------------------------
st.title("📹 AI YouTube Video Analyzer")
st.write("Analyze any YouTube video using AI and generate a detailed report.")

# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.header("ℹ️ About")
    st.write(
        """
        This AI application can:
        - 📄 Summarize YouTube videos
        - ⏱️ Generate timestamps
        - 🎯 Extract key points
        - 📝 Analyze video content
        """
    )

# ----------------------------
# Cache Agent
# ----------------------------
@st.cache_resource
def get_agent():
    return buil_youtube_agent()

agent = get_agent()

# ----------------------------
# Validate YouTube URL
# ----------------------------
def is_valid_youtube_url(url):
    pattern = r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$"
    return re.match(pattern, url)

def get_video_info(url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return {
            "title": info.get("title"),
            "channel": info.get("uploader"),
            "duration": info.get("duration"),
            "views": info.get("view_count"),
            "upload_date": info.get("upload_date"),
            "thumbnail": info.get("thumbnail")
        }

    except Exception:
        return None
def format_duration(seconds):
    if not seconds:
        return "Unknown"

    minutes = seconds // 60
    seconds = seconds % 60

    return f"{minutes} min {seconds} sec"


def create_pdf(content):
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("<b>AI YouTube Video Analysis Report</b>", styles["Title"]))
    story.append(Paragraph("<br/>", styles["Normal"]))

    for line in content.split("\n"):
        story.append(Paragraph(line, styles["BodyText"]))

    doc.build(story)

    buffer.seek(0)

    return buffer

# ----------------------------
# User Input
# ----------------------------
video_url = st.text_input(
    "🔗 Enter YouTube Video URL",
    placeholder="https://www.youtube.com/watch?v=..."
)

analysis_type = st.selectbox(
    "🎯 Choose Analysis Type",
    [
        "Summary",
        "Detailed Analysis",
        "Key Takeaways",
        "Study Notes",
        "Quiz"
    ]
)

button = st.button("🚀 Analyze Video")

# ----------------------------
# Analyze
# ----------------------------
if button:

    if not video_url:
        st.warning("⚠️ Please enter a YouTube video URL.")

    elif not is_valid_youtube_url(video_url):
        st.error("❌ Invalid YouTube URL. Please enter a valid YouTube link.")

    else:

        st.success("✅ Valid YouTube URL")

        video_info = get_video_info(video_url)

        if video_info:

            col1, col2 = st.columns([1, 2])

            with col1:
                if video_info["thumbnail"]:
                    st.image(video_info["thumbnail"], width="stretch")

            with col2:
                st.markdown("### 🎬 Video Information")

                st.write(f"**Title:** {video_info['title']}")
                st.write(f"**Channel:** {video_info['channel']}")
                st.write(f"**Duration:** {format_duration(video_info['duration'])}")

                views = video_info.get("views")

                if views:
                    st.write(f"**Views:** {views:,}")
                else:
                    st.write("**Views:** Not Available")

                upload = video_info["upload_date"]

                if upload:
                    upload = f"{upload[:4]}-{upload[4:6]}-{upload[6:]}"
                    st.write(f"**Upload Date:** {upload}")

        st.divider()

        progress_bar = st.progress(0)
        status = st.empty()

        status.text("🔍 Fetching video information...")
        progress_bar.progress(20)

        status.text("📜 Processing transcript...")
        progress_bar.progress(50)

        status.text("🤖 AI is analyzing the video...")
        progress_bar.progress(80)

        if analysis_type == "Summary":
            prompt = f"""
            Analyze the following YouTube video.

            URL:
            {video_url}

            Provide:
            - A concise summary
            - Main topics
            - Final conclusion
            """

        elif analysis_type == "Detailed Analysis":
            prompt = f"""
            Analyze the following YouTube video.

            URL:
            {video_url}

            Provide:
            - Complete explanation
            - Timestamps (only if available)
            - Important concepts
            - Examples
            - Final conclusion
            """

        elif analysis_type == "Key Takeaways":
            prompt = f"""
            Analyze the following YouTube video.

            URL:
            {video_url}

            Extract:
            - Top 10 key takeaways
            - Important insights
            - Actionable points
            """

        elif analysis_type == "Study Notes":
            prompt = f"""
            Analyze the following YouTube video.

            URL:
            {video_url}

            Create clean study notes with:
            - Headings
            - Bullet points
            - Important facts
            """

        else:   # Quiz
            prompt = f"""
            Analyze the following YouTube video.

            URL:
            {video_url}

            Create:
            - 10 Multiple Choice Questions
            - Correct answers
            - Short explanation for each answer
            """

        try:
            response = agent.run(prompt)

            pdf_file = create_pdf(response.content)

            progress_bar.progress(100)
            status.text("✅ Analysis Completed!")

            st.success("✅ Analysis Completed!")

            st.markdown("---")

            with st.expander("📄 Analysis Report", expanded=True):
                st.markdown(response.content)

            st.download_button(
                label="📥 Download Report (.txt)",
                data=response.content,
                file_name="youtube_analysis.txt",
                mime="text/plain"
            )

            st.download_button(
                label="📄 Download Report (PDF)",
                data=pdf_file,
                file_name="youtube_analysis.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            progress_bar.empty()
            status.empty()
            st.error(f"❌ An error occurred while analyzing the video:\n\n{e}")

        st.markdown("---")

        st.caption("Built with ❤️ using Streamlit + Agno + Groq")