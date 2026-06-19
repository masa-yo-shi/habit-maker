import asyncio
from datetime import date
from pathlib import Path
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import Base
import cruds.main as cruds
import timer_service


async def _make_session_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return engine, session_factory


def test_timer_manager_records_diary_entry_after_delay(tmp_path):
    async def run():
        engine, session_factory = await _make_session_factory(tmp_path)
        manager = timer_service.TimerManager(session_factory=session_factory)

        try:
            state = await manager.start_timer(
                habit="Reading",
                memo="One chapter",
                entry_date=date(2026, 6, 15),
                duration_seconds=0,
            )

            for _ in range(50):
                latest = await manager.get_timer(state.timer_id)
                if latest is not None and latest.status == "completed":
                    break
                await asyncio.sleep(0.02)

            latest = await manager.get_timer(state.timer_id)
            assert latest is not None
            assert latest.status == "completed"
            assert latest.diary_entry_id is not None

            async with session_factory() as session:
                entries = await cruds.get_diary_entries_by_date(session, date(2026, 6, 15))

            assert len(entries) == 1
            assert entries[0].title == "Reading"
            assert entries[0].content == "One chapter"
        finally:
            await engine.dispose()

    asyncio.run(run())
