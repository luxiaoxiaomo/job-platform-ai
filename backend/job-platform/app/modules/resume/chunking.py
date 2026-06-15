"""
Resume text chunking utilities.
"""
import hashlib


def estimate_token_count(text: str) -> int:
    """Cheap token estimate good enough for queueing and previews."""
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, len(stripped) // 2)


def hash_text(text: str) -> str:
    """Return SHA-256 hash for text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_resume_text(text: str, max_chars: int = 900) -> list[dict[str, object]]:
    """Split resume text into stable raw chunks."""
    paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        paragraph_len = len(paragraph)
        if current and current_len + paragraph_len + 1 > max_chars:
            chunks.append("\n".join(current))
            current = [paragraph]
            current_len = paragraph_len
        else:
            current.append(paragraph)
            current_len += paragraph_len + 1
    if current:
        chunks.append("\n".join(current))

    return [
        {
            "chunk_index": index,
            "section": "raw",
            "content": chunk,
            "content_hash": hash_text(chunk),
            "token_count": estimate_token_count(chunk),
        }
        for index, chunk in enumerate(chunks)
    ]
