"""Shared helpers for AI interview API routes."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import AIInterview, AIInterviewQA

VALID_FRONTEND_TYPES = frozenset({"technical", "hr", "comprehensive"})
MAX_QUESTIONS = 25


def normalize_request_interview_type(raw: str | None) -> str:
    """Normalize client interview type to a supported frontend value."""
    value = raw or "comprehensive"
    return value if value in VALID_FRONTEND_TYPES else "comprehensive"


def to_db_interview_type(frontend_type: str) -> str:
    """Map frontend type to DB column value."""
    return "behavioral" if frontend_type == "hr" else frontend_type


def to_frontend_interview_type(stored_type: str | None) -> str:
    """Map DB column value to frontend/API response type."""
    if stored_type == "behavioral":
        return "hr"
    return stored_type or "comprehensive"


async def fetch_last_qa(db: AsyncSession, interview_id: int) -> AIInterviewQA | None:
    stmt = (
        select(AIInterviewQA)
        .where(AIInterviewQA.interview_id == interview_id)
        .order_by(desc(AIInterviewQA.sequence))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@dataclass
class InterviewRoundState:
    interview: AIInterview
    interview_id: int
    thread_id: str
    is_first: bool
    next_sequence: int
    last_qa: AIInterviewQA | None
    limit_reached: bool


def interview_thread_id(user_id: int, interview_id: int) -> str:
    return f"user_{user_id}_interview_{interview_id}"


async def prepare_interview_round(
    db: AsyncSession,
    interview: AIInterview,
    user_id: int,
    user_message: str | None,
    *,
    commit_user_answer: bool,
) -> InterviewRoundState:
    """Load QA state and optionally persist the user's latest answer."""
    interview_id = interview.id
    last_qa = await fetch_last_qa(db, interview_id)
    is_first = last_qa is None

    if not is_first and user_message and last_qa is not None:
        last_qa.answer = user_message
        db.add(last_qa)
        if commit_user_answer:
            await db.commit()

    next_sequence = (last_qa.sequence + 1) if last_qa else 1
    limit_reached = next_sequence > MAX_QUESTIONS

    return InterviewRoundState(
        interview=interview,
        interview_id=interview_id,
        thread_id=interview_thread_id(user_id, interview_id),
        is_first=is_first,
        next_sequence=next_sequence,
        last_qa=last_qa,
        limit_reached=limit_reached,
    )


async def save_interview_question(
    db: AsyncSession,
    interview_id: int,
    sequence: int,
    question: str,
) -> None:
    """Persist a new interviewer question and update totals."""
    interview = await db.get(AIInterview, interview_id)
    if not interview:
        raise RuntimeError("面试会话不存在，无法保存提问")

    db.add(
        AIInterviewQA(
            interview_id=interview_id,
            sequence=sequence,
            question=question or "好的，我们继续下一题。",
        )
    )
    interview.total_questions = sequence
    await db.commit()
