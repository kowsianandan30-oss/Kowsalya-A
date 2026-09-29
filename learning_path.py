import json
import re

from gemini_client import generate_text


def extract_json(text: str):
    """Extract a JSON array from the AI response."""

    text = text.strip()

    # Remove markdown code fences if the AI adds them.
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError("Learning Path response is not valid JSON.")

    return json.loads(text[start:end + 1])


def build_learning_path_prompt(topic: str) -> str:
    """Create a prompt for generating a topic-specific learning path."""

    return f"""
You are EduGenie, an educational AI learning assistant.

Create a complete learning path for the following topic:

TOPIC:
{topic}

STRICT REQUIREMENTS:

1. Create exactly 7 learning steps.
2. Every step must be directly related to the requested topic.
3. Start from beginner-level fundamentals.
4. Progress gradually toward more advanced concepts.
5. Each step must be different.
6. Do not repeat the same concept.
7. Include practical learning or practice where appropriate.
8. The final step should help the student test or apply what they learned.
9. Use simple language suitable for a student.
10. Do not create generic steps unrelated to the topic.
11. Return ONLY valid JSON.
12. Do not include explanations outside the JSON.

Return the result in exactly this format:

[
  {{
    "step": 1,
    "title": "Step title",
    "description": "Short explanation of what the student should learn."
  }},
  {{
    "step": 2,
    "title": "Step title",
    "description": "Short explanation of what the student should learn."
  }},
  {{
    "step": 3,
    "title": "Step title",
    "description": "Short explanation of what the student should learn."
  }},
  {{
    "step": 4,
    "title": "Step title",
    "description": "Short explanation of what the student should learn."
  }},
  {{
    "step": 5,
    "title": "Step title",
    "description": "Short explanation of what the student should learn."
  }},
  {{
    "step": 6,
    "title": "Step title",
    "description": "Short explanation of what the student should learn."
  }},
  {{
    "step": 7,
    "title": "Step title",
    "description": "Short explanation of what the student should learn."
  }}
]
"""


def validate_learning_step(step: dict) -> bool:
    """Validate one learning-path step."""

    if not isinstance(step, dict):
        return False

    step_number = step.get("step")
    title = step.get("title")
    description = step.get("description")

    if not isinstance(step_number, int):
        return False

    if not isinstance(title, str) or not title.strip():
        return False

    if not isinstance(description, str) or not description.strip():
        return False

    return True


def get_learning_recommendations(topic: str) -> list:
    """
    Generate a 7-step learning path for the requested topic.
    """

    if not topic or not topic.strip():
        raise ValueError("Please enter a topic for the Learning Path.")

    topic = topic.strip()

    prompt = build_learning_path_prompt(topic)

    response = generate_text(prompt)

    try:
        learning_path = extract_json(response)
    except Exception as exc:
        raise RuntimeError(
            "The Learning Path generator returned invalid data. "
            "Please try again."
        ) from exc

    if not isinstance(learning_path, list):
        raise RuntimeError("Learning Path data must be a list.")

    valid_steps = []

    for item in learning_path:
        if validate_learning_step(item):
            valid_steps.append(item)

    # Remove duplicate step numbers.
    unique_steps = []
    seen_steps = set()

    for item in valid_steps:
        step_number = item["step"]

        if step_number in seen_steps:
            continue

        seen_steps.add(step_number)
        unique_steps.append(item)

    # Sort steps in learning order.
    unique_steps.sort(key=lambda item: item["step"])

    if len(unique_steps) < 7:
        raise RuntimeError(
            "Could not generate all 7 Learning Path steps. "
            "Please try again."
        )

    return unique_steps[:7]