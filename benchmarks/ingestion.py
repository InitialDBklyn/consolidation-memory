"""Load locomo10.json and ingest into MemoryClient instances."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger("benchmark.ingestion")

# LoCoMo category mapping (from the actual JSON, NOT the paper ordering):
# 1 = multi-hop, 2 = temporal, 3 = open-domain, 4 = single-hop, 5 = adversarial
CATEGORY_MAP = {
    1: "multi-hop",
    2: "temporal",
    3: "open-domain",
    4: "single-hop",
    5: "adversarial",
}


def load_dataset(data_path: Path) -> list[dict]:
    """Load locomo10.json and return the list of conversations."""
    locomo_file = data_path / "locomo10.json"
    if not locomo_file.exists():
        raise FileNotFoundError(
            f"locomo10.json not found at {locomo_file}. "
            f"Download from https://github.com/snap-research/locomo "
            f"and place in {data_path}/"
        )
    with open(locomo_file, encoding="utf-8") as f:
        data = json.load(f)
    logger.info("Loaded %d conversations from locomo10.json", len(data))
    return data


def get_speakers(conversation: dict) -> tuple[str, str]:
    """Extract the two speaker names from a conversation.

    LoCoMo format: conversation["conversation"] is a dict with
    "speaker_a" and "speaker_b" keys.
    """
    conv_data = conversation.get("conversation", {})
    speaker_a = conv_data.get("speaker_a", "Speaker A")
    speaker_b = conv_data.get("speaker_b", "Speaker B")
    return speaker_a, speaker_b


def _iter_sessions(conv_data: dict):
    """Yield (session_number, date_time_str, turns_list) for each session.

    LoCoMo format: sessions are keyed as session_1, session_2, ...
    with corresponding session_1_date_time, session_2_date_time, ...
    """
    # Find all session keys (session_N where N is a number)
    session_nums = sorted(
        int(m.group(1))
        for key in conv_data
        if (m := re.match(r"^session_(\d+)$", key))
    )
    for n in session_nums:
        turns = conv_data.get(f"session_{n}", [])
        date_time = conv_data.get(f"session_{n}_date_time", "")
        yield n, date_time, turns


def ingest_conversation(
    client,
    conversation: dict,
    sample_id: str,
) -> int:
    """Ingest all turns from a conversation into a MemoryClient.

    Each dialogue turn becomes an episode with session timestamps prepended.

    Returns:
        Number of episodes ingested.
    """
    count = 0
    conv_data = conversation.get("conversation", {})

    for session_num, date_time, turns in _iter_sessions(conv_data):
        for turn in turns:
            speaker = turn.get("speaker")
            if speaker is None:
                logger.warning(
                    "Turn in session %d missing speaker field, defaulting to 'Unknown'",
                    session_num,
                )
                speaker = "Unknown"

            text = turn.get("text", "")
            if not text:
                continue

            # Prepend timestamp for temporal question answering
            if date_time:
                content = f"[{date_time}] {speaker}: {text}"
            else:
                content = f"{speaker}: {text}"

            client.store(
                content=content,
                content_type="exchange",
                tags=[sample_id, f"session_{session_num}"],
                surprise=0.5,
            )
            count += 1

    logger.info("Ingested %d turns for %s", count, sample_id)
    return count


def get_qa_pairs(conversation: dict) -> list[dict]:
    """Extract QA pairs from a conversation, skipping adversarial (category 5).

    Returns list of dicts with keys: question, answer, category (int), category_name (str).
    """
    pairs = []
    for qa in conversation.get("qa", []):
        category = qa.get("category", 0)
        if isinstance(category, str):
            for k, v in CATEGORY_MAP.items():
                if v == category.lower():
                    category = k
                    break
            else:
                logger.warning("Skipping QA pair with unmapped category: %r", category)
                continue

        if category == 5:  # Skip adversarial
            continue

        question = qa.get("question", "")
        answer = qa.get("answer", "")

        # Some answers are ints (e.g., 2022) — convert to string
        if isinstance(answer, (int, float)):
            answer = str(answer)

        if not question or not answer:
            continue

        pairs.append({
            "question": question,
            "answer": answer,
            "category": category,
            "category_name": CATEGORY_MAP.get(category, f"unknown_{category}"),
        })

    return pairs
