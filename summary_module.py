def summarize_text(text: str) -> str:
    words = text.split()
    summary = " ".join(words[:40])
    return summary + ("..." if len(words) > 40 else "")
