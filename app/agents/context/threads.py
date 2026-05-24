"""Thread id derivation helpers for agent chains."""

from __future__ import annotations


def build_sub_agent_thread(parent_thread_id: str, role: str, user_id: int) -> str:
    if parent_thread_id:
        return f"{parent_thread_id}:{role}"
    return f"user_{user_id}_{role}"


def list_related_threads(parent_thread_id: str, user_id: int) -> list[str]:
    """Threads to clear when a conversation is reset."""
    related = [
        build_sub_agent_thread(parent_thread_id, "resume", user_id),
        build_sub_agent_thread(parent_thread_id, "career", user_id),
        f"{parent_thread_id}:memory",
        f"{parent_thread_id}_auto",
        f"{parent_thread_id}_clear",
        build_sub_agent_thread("", "resume", user_id),
        build_sub_agent_thread("", "career", user_id),
        f"user_{user_id}_memory",
    ]
    # dedupe while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for tid in related:
        if tid not in seen:
            seen.add(tid)
            ordered.append(tid)
    return ordered
