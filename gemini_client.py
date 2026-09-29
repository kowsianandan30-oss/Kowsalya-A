import os
import time
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

DEMO_MODE = os.getenv("DEMO_MODE", "True").strip().lower() == "true"


def get_topic_from_prompt(prompt: str) -> str:
    """Extract the topic from the prompt."""

    patterns = [
        r"TOPIC:\s*(.+)",
        r"topic:\s*(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)

        if match:
            topic = match.group(1).strip()

            # Stop at the next line if extra instructions follow.
            topic = topic.split("\n")[0].strip()

            if topic:
                return topic

    return "the selected topic"


def demo_learning_path(prompt: str) -> str:
    """Create an offline 7-step Learning Path."""

    topic = get_topic_from_prompt(prompt)

    return f"""
[
  {{
    "step": 1,
    "title": "Learn the Basics of {topic}",
    "description": "Understand the meaning, purpose, and basic terminology of {topic}."
  }},
  {{
    "step": 2,
    "title": "Understand the Core Concepts",
    "description": "Study the main concepts and fundamental principles of {topic}."
  }},
  {{
    "step": 3,
    "title": "Explore Important Components",
    "description": "Learn the important parts, methods, features, or ideas related to {topic}."
  }},
  {{
    "step": 4,
    "title": "Study Practical Examples",
    "description": "Understand how {topic} is used through simple practical and real-world examples."
  }},
  {{
    "step": 5,
    "title": "Practice {topic}",
    "description": "Strengthen your understanding by solving exercises and practicing important concepts."
  }},
  {{
    "step": 6,
    "title": "Build a Small Project",
    "description": "Apply your knowledge of {topic} by creating a small practical project or activity."
  }},
  {{
    "step": 7,
    "title": "Review and Test Your Knowledge",
    "description": "Review the important concepts of {topic} and test your understanding with questions or a quiz."
  }}
]
"""


def demo_quiz(prompt: str) -> str:
    """Create an offline demo quiz."""

    topic = get_topic_from_prompt(prompt)

    return f"""
[
  {{
    "question": "What is an important first step when learning {topic}?",
    "options": [
      "Understanding the basic concepts",
      "Deleting the study material",
      "Changing the computer wallpaper",
      "Turning off the computer"
    ],
    "answer": "Understanding the basic concepts"
  }},
  {{
    "question": "Which activity can help a student learn {topic} better?",
    "options": [
      "Practicing examples",
      "Deleting notes",
      "Ignoring the topic",
      "Closing every application"
    ],
    "answer": "Practicing examples"
  }},
  {{
    "question": "Why are practical examples useful when studying {topic}?",
    "options": [
      "They connect concepts with real situations",
      "They increase internet speed",
      "They change the operating system",
      "They automatically install software"
    ],
    "answer": "They connect concepts with real situations"
  }},
  {{
    "question": "What is a good way to check your understanding of {topic}?",
    "options": [
      "Answer questions and apply the concepts",
      "Delete the learning material",
      "Restart the computer repeatedly",
      "Change the desktop background"
    ],
    "answer": "Answer questions and apply the concepts"
  }},
  {{
    "question": "What should a learner do after studying the basics of {topic}?",
    "options": [
      "Practice and apply the concepts",
      "Stop learning immediately",
      "Delete the notes",
      "Remove the learning material"
    ],
    "answer": "Practice and apply the concepts"
  }}
]
"""


def demo_explanation(prompt: str) -> str:
    """Create an offline explanation."""

    topic = get_topic_from_prompt(prompt)

    return f"""
Definition:
{topic} can be understood by learning its basic meaning,
purpose, and important concepts.

How it works:
The main ideas of {topic} can be connected together to
understand how it works in practical situations.

Example:
A simple real-world example can help connect {topic}
with practical use.

Key Points:
• Learn the basics.
• Understand the core concepts.
• Study practical examples.
• Practice the topic.
"""


def demo_summary(prompt: str) -> str:
    """Create an offline summary."""

    topic = get_topic_from_prompt(prompt)

    return f"""
Summary of {topic}:

{topic} can be understood by learning its basic concepts,
important principles, practical examples, and applications.

Key Points:
• Understand the fundamentals.
• Learn the important concepts.
• Study practical examples.
• Practice what you learn.
• Review your knowledge.
"""


def demo_response(prompt: str) -> str:
    """
    Handle all offline Demo Mode responses.
    """

    prompt_lower = prompt.lower()

    # IMPORTANT:
    # Learning Path must be checked BEFORE generic "explain".
    if (
        "learning path" in prompt_lower
        or "learning_path" in prompt_lower
        or "learning recommendations" in prompt_lower
        or "learning recommendations" in prompt_lower
    ):
        print("DEMO_MODE -> Using offline Learning Path.")
        return demo_learning_path(prompt)

    # Quiz
    if "quiz" in prompt_lower:
        print("DEMO_MODE -> Using offline Quiz.")
        return demo_quiz(prompt)

    # Summary
    if "summar" in prompt_lower:
        print("DEMO_MODE -> Using offline Summary.")
        return demo_summary(prompt)

    # Explanation
    if "explain" in prompt_lower:
        print("DEMO_MODE -> Using offline Explanation.")
        return demo_explanation(prompt)

    # Default Q&A response
    topic = get_topic_from_prompt(prompt)

    print("DEMO_MODE -> Using offline Q&A response.")

    return f"""
EduGenie Demo Mode:

You asked about:
{topic}

EduGenie is currently running without the Gemini API.

The application is working correctly in Demo Mode.
"""


def generate_text(prompt: str) -> str:
    """
    Generate text using Gemini or offline Demo Mode.
    """

    # ------------------------------------------------
    # DEMO MODE
    # ------------------------------------------------
    # When True, Gemini is NOT contacted.
    # This avoids the exhausted API quota.
    # ------------------------------------------------

    if DEMO_MODE:
        return demo_response(prompt)

    # ------------------------------------------------
    # GEMINI MODE
    # ------------------------------------------------

    if not API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Please add your Gemini API key to the .env file."
        )

    client = genai.Client(api_key=API_KEY)

    max_attempts = 3
    wait_seconds = 2

    for attempt in range(1, max_attempts + 1):

        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
            )

            if response is None:
                raise RuntimeError(
                    "Gemini returned no response."
                )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text

        except Exception as exc:

            error_message = str(exc)

            # Gemini quota error
            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):
                raise RuntimeError(
                    "Gemini API quota has been exhausted. "
                    "Set DEMO_MODE=True in the .env file "
                    "to continue using EduGenie in Demo Mode."
                ) from exc

            # Temporary Gemini server error
            if (
                "503" in error_message
                or "UNAVAILABLE" in error_message
            ):

                if attempt < max_attempts:
                    print(
                        f"Gemini is temporarily unavailable. "
                        f"Retrying in {wait_seconds} seconds..."
                    )

                    time.sleep(wait_seconds)

                    wait_seconds *= 2

                    continue

                raise RuntimeError(
                    "Gemini is temporarily unavailable. "
                    "Please try again later."
                ) from exc

            # Network / DNS error
            if (
                "11001" in error_message
                or "getaddrinfo failed" in error_message
            ):
                raise RuntimeError(
                    "Network/DNS error while connecting to Gemini. "
                    "Check your internet connection or use "
                    "DEMO_MODE=True."
                ) from exc

            raise RuntimeError(
                f"Gemini API error: {error_message}"
            ) from exc

    raise RuntimeError("Gemini request failed.")