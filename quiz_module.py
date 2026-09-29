import json
import re

from gemini_client import generate_text


def clean_question(question: str) -> str:
    """Normalize a question so duplicate checking is reliable."""
    question = question.strip().lower()
    question = re.sub(r"\s+", " ", question)
    question = re.sub(r"[^\w\s]", "", question)
    return question


def remove_duplicate_questions(questions: list) -> list:
    """Remove duplicate questions while preserving order."""

    unique_questions = []
    seen = set()

    for item in questions:
        if not isinstance(item, dict):
            continue

        question = item.get("question", "")

        if not question:
            continue

        key = clean_question(question)

        if key in seen:
            continue

        seen.add(key)
        unique_questions.append(item)

    return unique_questions


def build_quiz_prompt(topic: str, number_of_questions: int = 5) -> str:
    return f"""
You are EduGenie, an educational quiz generator.

Create a quiz about this topic:

TOPIC:
{topic}

STRICT REQUIREMENTS:

1. Create exactly {number_of_questions} questions.
2. Every question must be different.
3. Do NOT repeat the same question using different wording.
4. Each question must test a different concept, fact, relationship, example, or application within the topic.
5. Every question must have exactly 4 answer options.
6. Only one option must be correct.
7. The questions must stay focused on the requested topic.
8. Do not create generic questions unrelated to the topic.
9. Use clear language suitable for a student.
10. Do not include explanations outside the JSON.

Return ONLY valid JSON in this exact structure:

[
  {{
    "question": "Question 1",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": "The exact correct option"
  }},
  {{
    "question": "Question 2",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": "The exact correct option"
  }}
]

Make sure all {number_of_questions} questions are unique.
"""


def extract_json(text: str):
    """Extract a JSON array from Gemini output."""

    text = text.strip()

    # Remove markdown code fences if Gemini adds them.
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError("Gemini did not return a valid quiz JSON array.")

    json_text = text[start:end + 1]

    return json.loads(json_text)


def validate_question(question: dict) -> bool:
    """Validate one quiz question."""

    if not isinstance(question, dict):
        return False

    question_text = question.get("question")
    options = question.get("options")
    answer = question.get("answer")

    if not isinstance(question_text, str) or not question_text.strip():
        return False

    if not isinstance(options, list) or len(options) != 4:
        return False

    if not all(isinstance(option, str) and option.strip() for option in options):
        return False

    if not isinstance(answer, str) or not answer.strip():
        return False

    if answer not in options:
        return False

    return True


def generate_quiz(topic: str, num_questions: int = 5) -> list:
    """
    Generate a quiz with unique questions.

    The system always aims for exactly 5 questions.
    Duplicate questions are removed automatically.
    """

    # Always use 5 for the EduGenie quiz requirement.
    number_of_questions = 5

    if not topic or not topic.strip():
        raise ValueError("Please enter a topic for the quiz.")

    topic = topic.strip()

    all_questions = []

    # First request.
    prompt = build_quiz_prompt(topic, number_of_questions)

    response = generate_text(prompt)

    try:
        questions = extract_json(response)
    except Exception as exc:
        raise RuntimeError(
            "The quiz generator returned invalid data. Please try again."
        ) from exc

    if not isinstance(questions, list):
        raise RuntimeError("Quiz data must be a list of questions.")

    # Validate and collect questions.
    for question in questions:
        if validate_question(question):
            all_questions.append(question)

    # Remove duplicates.
    all_questions = remove_duplicate_questions(all_questions)

    # If we already have 5 unique questions, return them.
    if len(all_questions) >= number_of_questions:
        return all_questions[:number_of_questions]

    # Ask for replacement questions if duplicates or missing questions occurred.
    attempts = 0
    max_attempts = 3

    while len(all_questions) < number_of_questions and attempts < max_attempts:

        remaining = number_of_questions - len(all_questions)

        used_questions = "\n".join(
            f"- {item['question']}"
            for item in all_questions
        )

        replacement_prompt = f"""
You are EduGenie.

The student requested a quiz about:

{topic}

We already have these questions:

{used_questions}

Generate exactly {remaining} NEW questions.

STRICT REQUIREMENTS:

- Do NOT repeat any question listed above.
- Do NOT simply reword an existing question.
- Each new question must test a different concept, fact, relationship, example, or application.
- Every question must have exactly 4 options.
- Only one option must be correct.
- Stay completely within the topic: {topic}.
- Return ONLY valid JSON.

Format:

[
  {{
    "question": "New question",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": "The exact correct option"
  }}
]
"""

        replacement_response = generate_text(replacement_prompt)

        try:
            replacement_questions = extract_json(replacement_response)
        except Exception:
            attempts += 1
            continue

        if not isinstance(replacement_questions, list):
            attempts += 1
            continue

        for question in replacement_questions:
            if validate_question(question):
                all_questions.append(question)

        # Remove duplicates again after every replacement attempt.
        all_questions = remove_duplicate_questions(all_questions)

        attempts += 1

    # Final validation.
    all_questions = remove_duplicate_questions(all_questions)

    if len(all_questions) < number_of_questions:
        raise RuntimeError(
            "Could not generate 5 different questions for this topic. "
            "Please try the quiz again."
        )

    return all_questions[:number_of_questions]