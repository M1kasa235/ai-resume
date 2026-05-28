"""Tests for memory event lifecycle (claim, recovery, round counters)."""

import asyncio
from pathlib import Path

import pytest
import pytest_asyncio

from app.agents.memory.base import MemoryStoreBase
from app.agents.memory.service import MemoryService


@pytest_asyncio.fixture
async def memory_svc(tmp_path: Path):
    MemoryStoreBase._instance = None
    MemoryStoreBase._context_cache.clear()
    db_path = tmp_path / "memory_test.db"
    svc = MemoryService(db_path=str(db_path))
    await svc._ensure_table()
    yield svc
    await MemoryService.shutdown()


@pytest.mark.asyncio
async def test_process_event_atomic_claim(memory_svc: MemoryService):
    event_id = await memory_svc.enqueue_event(
        user_id=1,
        thread_id="t1",
        event_type="manual_extract",
        payload={"transcript": "hello", "source": "test"},
        source="test",
    )

    class FakeLLM:
        async def ainvoke(self, _prompt):
            class Resp:
                content = '{"upsert": [], "delete": []}'
            return Resp()

    llm = FakeLLM()
    first = asyncio.create_task(memory_svc.process_event(event_id, llm=llm))
    second = asyncio.create_task(memory_svc.process_event(event_id, llm=llm))
    results = await asyncio.gather(first, second)

    successes = [r for r in results if r is not None]
    assert len(successes) == 1
    event = await memory_svc.get_event(event_id)
    assert event["status"] == "done"


@pytest.mark.asyncio
async def test_recover_stuck_processing_events(memory_svc: MemoryService):
    event_id = await memory_svc.enqueue_event(
        user_id=2,
        thread_id="t2",
        event_type="manual_extract",
        payload={"transcript": "stuck", "source": "test"},
        source="test",
    )
    conn = await memory_svc._get_conn()
    await conn.execute(
        """
        UPDATE memory_events
        SET status='processing',
            updated_at=datetime('now', '-10 minutes')
        WHERE id=?
        """,
        (event_id,),
    )
    await conn.commit()

    recovered = await memory_svc.recover_stuck_processing_events(stale_minutes=5)
    assert recovered == 1
    event = await memory_svc.get_event(event_id)
    assert event["status"] == "failed"


@pytest.mark.asyncio
async def test_increment_thread_round_persists(memory_svc: MemoryService):
    thread_id = "user_1_default"
    for _ in range(9):
        triggered = await memory_svc.increment_thread_round(thread_id, trigger_every=10)
        assert triggered is False

    triggered = await memory_svc.increment_thread_round(thread_id, trigger_every=10)
    assert triggered is True

    conn = await memory_svc._get_conn()
    rows = await conn.execute_fetchall(
        "SELECT round_count FROM memory_thread_counters WHERE thread_id=?",
        (thread_id,),
    )
    assert int(rows[0]["round_count"]) == 0


@pytest.mark.asyncio
async def test_reset_thread_round_counters(memory_svc: MemoryService):
    thread_id = "user_1_clear"
    await memory_svc.increment_thread_round(thread_id, trigger_every=100)
    await memory_svc.reset_thread_round_counters(thread_id)

    conn = await memory_svc._get_conn()
    rows = await conn.execute_fetchall(
        "SELECT round_count FROM memory_thread_counters WHERE thread_id=?",
        (thread_id,),
    )
    assert rows == []
