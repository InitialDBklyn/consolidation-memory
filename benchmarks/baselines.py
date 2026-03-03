"""Full-context baseline — entire conversation stuffed into prompt."""

from __future__ import annotations

import logging

from openai import OpenAI

from benchmarks.ingestion import _iter_sessions
from benchmarks.prompts import FULL_CONTEXT_SYSTEM, FULL_CONTEXT_USER

logger = logging.getLogger("benchmark.baselines")


def build_transcript(conversation: dict) -> str:
    """Build a full text transcript from a conversation.

    LoCoMo format: conversation["conversation"] is a dict with
    session_N / session_N_date_time keys.
    """
    lines = []
    conv_data = conversation.get("conversation", {})

    for session_num, date_time, turns in _iter_sessions(conv_data):
        if date_time:
            lines.append(f"\n--- Session {session_num}: {date_time} ---\n")

        for turn in turns:
            speaker = turn.get("speaker", "Unknown")
            text = turn.get("text", "")
            if text:
                lines.append(f"{speaker}: {text}")

    return "\n".join(lines)


def answer_full_context(
    openai_client: OpenAI,
    transcript: str,
    question: str,
    speaker_a: str,
    speaker_b: str,
    model: str = "gpt-4o-mini",
) -> str:
    """Answer a question using the full conversation transcript.

    Args:
        openai_client: OpenAI client instance.
        transcript: Full conversation text.
        question: The question to answer.
        speaker_a: First speaker name.
        speaker_b: Second speaker name.
        model: OpenAI model to use.

    Returns:
        The predicted answer string.
    """
    prompt = FULL_CONTEXT_USER.format(
        speaker_a=speaker_a,
        speaker_b=speaker_b,
        transcript=transcript,
        question=question,
    )

    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": FULL_CONTEXT_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=50,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("OpenAI API error for full-context: %s", e)
        answer = ""

    return answer
