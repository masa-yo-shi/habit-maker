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
import models.main as models
from shcemas.main import DiaryEntryCreateSchema, DiaryEntryUpdateSchema


async def _make_session(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = session_factory()
    return engine, session


def test_create_update_and_delete_diary_entry(tmp_path):
    async def run():
        engine, db_session = await _make_session(tmp_path)
        try:
            created = await cruds.create_diary_entry(
                db_session,
                DiaryEntryCreateSchema(entry_date=date(2026, 6, 15), title="Diary", content="First entry"),
            )

            assert created.id is not None
            assert created.title == "Diary"

            updated = await cruds.update_diary_entry(
                db_session,
                DiaryEntryUpdateSchema(
                    id=created.id,
                    entry_date=date(2026, 6, 16),
                    title="Diary updated",
                    content="Second entry",
                ),
            )

            assert updated.entry_date == date(2026, 6, 16)
            assert updated.title == "Diary updated"

            by_date = await cruds.get_diary_entries_by_date(db_session, date(2026, 6, 16))
            assert len(by_date) == 1
            assert by_date[0].id == created.id

            await cruds.delete_diary_entry(db_session, created.id)
            assert await cruds.get_diary_entries_by_date(db_session, date(2026, 6, 16)) == []
        finally:
            await db_session.close()
            await engine.dispose()

    asyncio.run(run())


def test_calendar_month_summary_groups_entries_by_day(tmp_path):
    async def run():
        engine, db_session = await _make_session(tmp_path)
        try:
            db_session.add_all(
                [
                    models.DiaryEntry(entry_date=date(2026, 6, 1), title="One", content="A"),
                    models.DiaryEntry(entry_date=date(2026, 6, 1), title="Two", content="B"),
                    models.DiaryEntry(entry_date=date(2026, 6, 15), title="Three", content="C"),
                ]
            )
            await db_session.commit()

            summary = await cruds.get_calendar_month_summary(db_session, 2026, 6)

            assert summary.year == 2026
            assert summary.month == 6
            assert len(summary.days) == 30
            first_day = next(day for day in summary.days if day.entry_date == date(2026, 6, 1))
            mid_month = next(day for day in summary.days if day.entry_date == date(2026, 6, 15))

            assert first_day.entry_count == 2
            assert first_day.titles == ["One", "Two"]
            assert mid_month.entry_count == 1
        finally:
            await db_session.close()
            await engine.dispose()

    asyncio.run(run())
