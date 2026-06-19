import asyncio
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable
from uuid import uuid4

import cruds.main as habit_cruds
import db
from shcemas.main import DiaryEntryCreateSchema, TimerStatusSchema


@dataclass
class TimerState:
    timer_id: str
    user_id: int
    habit: str
    memo: str
    entry_date: date
    duration_seconds: int
    started_at: datetime
    scheduled_for: datetime
    status: str = "running"
    diary_entry_id: int | None = None
    error: str | None = None
    task: asyncio.Task[None] | None = None

    def remaining_seconds(self) -> int:
        if self.status != "running":
            return 0
        remaining = int((self.scheduled_for - datetime.now(timezone.utc)).total_seconds())
        return max(0, remaining)


class TimerManager:
    def __init__(
        self,
        session_factory: Callable[[], object] = db.async_session,
    ) -> None:
        self._session_factory = session_factory
        self._timers: dict[str, TimerState] = {}
        self._lock = asyncio.Lock()

    async def start_timer(
        self,
        *,
        user_id: int,
        habit: str,
        memo: str,
        entry_date: date,
        duration_seconds: int,
    ) -> TimerState:
        timer_id = uuid4().hex
        started_at = datetime.now(timezone.utc)
        scheduled_for = started_at + timedelta(seconds=duration_seconds)
        state = TimerState(
            timer_id=timer_id,
            user_id=user_id,
            habit=habit,
            memo=memo,
            entry_date=entry_date,
            duration_seconds=duration_seconds,
            started_at=started_at,
            scheduled_for=scheduled_for,
        )

        async with self._lock:
            self._timers[timer_id] = state

        state.task = asyncio.create_task(self._run_timer(timer_id))
        return state

    async def get_timer(self, timer_id: str) -> TimerState | None:
        async with self._lock:
            return self._timers.get(timer_id)

    async def _run_timer(self, timer_id: str) -> None:
        state = await self.get_timer(timer_id)
        if state is None:
            return

        try:
            await asyncio.sleep(state.duration_seconds)
            async with self._session_factory() as session:
                created = await habit_cruds.create_diary_entry(
                    session,
                    DiaryEntryCreateSchema(
                        entry_date=state.entry_date,
                        title=state.habit,
                        content=state.memo,
                    ),
                    state.user_id,
                )
            async with self._lock:
                state.status = "completed"
                state.diary_entry_id = created.id
                state.error = None
        except Exception as exc:  # pragma: no cover - defensive
            async with self._lock:
                state.status = "failed"
                state.error = str(exc)

    def to_status_schema(self, state: TimerState) -> TimerStatusSchema:
        return TimerStatusSchema(
            timer_id=state.timer_id,
            status=state.status,
            habit=state.habit,
            memo=state.memo,
            entry_date=state.entry_date,
            duration_seconds=state.duration_seconds,
            started_at=state.started_at,
            scheduled_for=state.scheduled_for,
            remaining_seconds=state.remaining_seconds(),
            diary_entry_id=state.diary_entry_id,
            error=state.error,
        )


timer_manager = TimerManager()
