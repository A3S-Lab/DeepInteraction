from typing import List, Tuple, Optional
import math
import os
import re
from openai import OpenAI

# =========================
# Client & embedding helper
# =========================
client = OpenAI(
    api_key=os.environ.get("DASHSCOPE_API_KEY", ""),
    base_url=os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
)

def get_text_embedding(text: str) -> List[float]:
    """provided embedding wrapper (text-embedding-v4)."""
    resp = client.embeddings.create(
        model="text-embedding-v4",
        input=text,
        # dimensions=1024,
        encoding_format="float"
    )
    return resp.data[0].embedding

def get_batch_embeddings(texts: List[str]) -> List[List[float]]:
    """Optional: batched embedding to reduce round-trips if service supports list input."""
    if not texts:
        return []
    resp = client.embeddings.create(
        model="text-embedding-v4",
        input=texts,                # multiple inputs in one call
        encoding_format="float"
    )
    # Ensure order is preserved
    return [item.embedding for item in resp.data]

# ===============
# Utility methods
# ===============
def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)

def split_sentences(text: str) -> List[str]:
    """
    Lightweight sentence splitter for mixed Chinese/English.
    Splits on 。！？；.!?; and newlines. Keeps punctuation with the sentence.
    Improved to handle numbers and abbreviations better.
    """
    import re  # Import here to avoid issues

    if not text:
        return []
    t = re.sub(r'\s+', ' ', text.strip())

    # More careful sentence splitting - avoid splitting on decimal points in numbers
    # Pattern: split on sentence endings but not on decimal numbers
    # Split on sentence endings, but be careful with abbreviations and numbers
    # This is a simplified approach - in production you'd want a more sophisticated sentence splitter
    sentences = re.split(r'(?<=[.!?;])\s+', t)

    # Clean up and filter
    parts = []
    for sent in sentences:
        sent = sent.strip()
        if sent and len(sent) > 1:  # Avoid very short fragments
            parts.append(sent)

    return parts if parts else [text.strip()]

def select_by_ratio_and_threshold(
    scored: List[Tuple[int, str, float]],
    keep_ratio: float = 0.5,
    min_similarity: float = 0.3,
    max_sentences: Optional[int] = None
) -> List[Tuple[int, str, float]]:
    """
    scored: list of (idx, sentence, similarity)
    Returns kept items in original order.
    """
    if not scored:
        return []

    # Threshold filter
    filtered = [(i, s, sc) for (i, s, sc) in scored if sc >= min_similarity]
    if not filtered:
        return []

    # Rank by similarity desc
    ranked = sorted(filtered, key=lambda x: x[2], reverse=True)

    # Compute how many to keep
    k = max(1, int(round(len(ranked) * keep_ratio)))
    keep_top = ranked[:k]

    # Optional absolute cap
    if max_sentences is not None:
        keep_top = keep_top[:max_sentences]

    # Restore original order by index
    keep_top.sort(key=lambda x: x[0])
    return keep_top

def build_filtered_answer(
    Q: str,
    A: str,
    keep_ratio: float = 0.5,
    min_similarity: float = 0.3,
    max_sentences: Optional[int] = None,
    joiner: str = " "
) -> Tuple[str, List[Tuple[str, float]]]:
    """
    Returns:
      A_prime (str): filtered answer joined by `joiner`
      details (List[Tuple[sentence, similarity]]): kept sentences with scores (in original order)
    """
    # 1) Embed Q
    q_vec = get_text_embedding(Q)

    # 2) Split A into sentences
    sentences = split_sentences(A)

    # 3) Embed sentences (batched for efficiency; fallback to single if you prefer)
    sent_vecs = get_batch_embeddings(sentences)

    # 4) Score each sentence
    scored: List[Tuple[int, str, float]] = []
    for i, (s, v) in enumerate(zip(sentences, sent_vecs)):
        sim = cosine_similarity(q_vec, v)
        scored.append((i, s, sim))

    # 5) Select by ratio + threshold, keep original order
    kept = select_by_ratio_and_threshold(
        scored,
        keep_ratio=keep_ratio,
        min_similarity=min_similarity,
        max_sentences=max_sentences
    )

    # 6) Join
    A_prime = joiner.join(s for _, s, _ in kept).strip()
    details = [(s, sc) for _, s, sc in kept]
    return A_prime, details

# =========================
# Example usage
# =========================
if __name__ == "__main__":
    Q = ""
    A = (
        ""
    )

    keep_ratio = 0.8
    min_similarity = 0.35
    max_sentences = None

    A_prime, details = build_filtered_answer(
        Q, A,
        keep_ratio=keep_ratio,
        min_similarity=min_similarity,
        max_sentences=max_sentences,
        joiner=" "
    )

    print("Filtered A':", A_prime)
    print("Kept sentences & similarity:")
    for s, sc in details:
        print(f"- {sc:.3f}: {s}")