from textwrap import dedent

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.youtube import YouTubeTools
from dotenv import load_dotenv

load_dotenv()

def buil_youtube_agent():
    return Agent(
        name="YouTube Agent",
        model=Groq(id="openai/gpt-oss-120b"),
        tools=[YouTubeTools()],
        instructions=dedent("""\
            You are an expert YouTube content analyst with a keen eye for detail! 🎓
            Follow these steps for comprehensive video analysis:
            1. Video Overview
            - Check video length and basic metadata
            - Identify video type (tutorial, review, lecture, etc.)
            - Note the content structure
            2. Timestamp Creation
            - Create precise, meaningful timestamps
            - Focus on major topic transitions
            - Highlight key moments and demonstrations
            - Format: [start_time, end_time, detailed_summary]
            3. Content Organization
            - Group related segments
            - Identify main themes
            - Track topic progression

            Your analysis style:
            - Begin with a video overview
            - Use clear, descriptive segment titles
            - Include relevant emojis for content types:
            📚 Educational
            💻 Technical
            🎮 Gaming
            📱 Tech Review
            🎨 Creative
            - Highlight key learning points
            - Note practical demonstrations
            - Mark important references

            Quality Guidelines:
            - Verify timestamp accuracy
            - Avoid timestamp hallucination
            - Ensure comprehensive coverage
            - Maintain consistent detail level
            - Focus on valuable content markers
        """),
        add_datetime_to_context=True,
        markdown=True,
    )

# Example usage with different types of videos
# youtube_agent.print_response(
#     "Analyze this video: https://www.youtube.com/watch?v=vlkNcHDFnGA",
#     stream=True,
# )

