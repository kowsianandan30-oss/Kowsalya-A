from gemini_client import generate_text


def explain_concept(text: str) -> str:
    prompt = f"""
You are EduGenie, an educational AI assistant.

Explain the following topic to a student in simple and clear language.

Topic:
{text}

Include:
1. A simple definition
2. How it works
3. A simple real-world example
4. Key points to remember

Use easy-to-understand language and clear formatting.
"""

    return generate_text(prompt)