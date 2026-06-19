from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import shcemas.main as main_schemas
import models.main as main_models

async def get_habits(db: AsyncSession, user_id: int) -> list[main_schemas.HabitSchema]:
    result = await db.execute(select(main_models.Habit).where(main_models.Habit.user_id == user_id))
    habits = result.scalars().all()
    return habits


async def get_habit_by_id(db: AsyncSession, habit_id: int, user_id: int) -> main_models.Habit | None:
    result = await db.execute(
        select(main_models.Habit).where(
            main_models.Habit.id == habit_id, main_models.Habit.user_id == user_id
        )
    )
    return result.scalar_one_or_none()

async def get_habit_by_category(db: AsyncSession, category: str, user_id: int) -> list[main_schemas.HabitSchema]:
    if category not in ["Health", "Personal Development", "Mental Health", "Original", "My Habits"]:
        raise ValueError("Invalid category. Must be one of: 'Health', 'Personal Development', 'Mental Health', 'Original', 'My Habits'.")
    result = await db.execute(
        select(main_models.Habit).where(
            main_models.Habit.category == category, main_models.Habit.user_id == user_id
        )
    )
    habits = result.scalars().all()
    return habits

async def create_habit(db: AsyncSession, habit: main_schemas.HabitCreateSchema, user_id: int) -> main_schemas.HabitSchema:
    new_habit = main_models.Habit(name=habit.name, description=habit.description, category=habit.category, user_id=user_id)
    db.add(new_habit)
    await db.commit()
    await db.refresh(new_habit)
    return new_habit

async def update_habit(db: AsyncSession, habit: main_schemas.HabitUpdateSchema, user_id: int) -> main_schemas.HabitSchema:
    result = await db.execute(
        select(main_models.Habit).where(
            main_models.Habit.id == habit.id, main_models.Habit.user_id == user_id
        )
    )
    existing_habit = result.scalar_one_or_none()

    if existing_habit is None:
        raise ValueError(f"Habit with id {habit.id} not found.")

    existing_habit.name = habit.name
    existing_habit.description = habit.description
    existing_habit.category = habit.category

    await db.commit()
    await db.refresh(existing_habit)
    return existing_habit

async def delete_habit(db: AsyncSession, habit_id: int, user_id: int) -> None:
    result = await db.execute(
        select(main_models.Habit).where(
            main_models.Habit.id == habit_id, main_models.Habit.user_id == user_id
        )
    )
    existing_habit = result.scalar_one_or_none()

    if existing_habit is None:
        raise ValueError(f"Habit with id {habit_id} not found.")

    await db.delete(existing_habit)
    await db.commit()
# カレンダー

async def get_calendar_memos(db: AsyncSession, user_id: int) -> list[main_schemas.CalendarMemoSchema]:
    result = await db.execute(
        select(main_models.CalendarMemo).where(main_models.CalendarMemo.user_id == user_id)
    )
    memos = result.scalars().all()
    return memos

async def get_calendar_memo_by_date(db: AsyncSession, memo_date, user_id: int) -> main_schemas.CalendarMemoSchema:
    result = await db.execute(
        select(main_models.CalendarMemo).where(
            main_models.CalendarMemo.memo_date == memo_date, main_models.CalendarMemo.user_id == user_id
        )
    )
    memo = result.scalar_one_or_none()
    return memo

async def create_calendar_memo(db: AsyncSession, memo: main_schemas.CalendarMemoCreateSchema, user_id: int) -> main_schemas.CalendarMemoSchema:
    new_memo = main_models.CalendarMemo(memo_date=memo.memo_date, content=memo.content, user_id=user_id)
    db.add(new_memo)
    await db.commit()
    await db.refresh(new_memo)
    return new_memo

async def update_calendar_memo(db: AsyncSession, memo: main_schemas.CalendarMemoUpdateSchema, user_id: int) -> main_schemas.CalendarMemoSchema:
    result = await db.execute(
        select(main_models.CalendarMemo).where(
            main_models.CalendarMemo.id == memo.id, main_models.CalendarMemo.user_id == user_id
        )
    )
    existing_memo = result.scalar_one_or_none()

    if existing_memo is None:
        raise ValueError(f"CalendarMemo with id {memo.id} not found.")

    existing_memo.memo_date = memo.memo_date
    existing_memo.content = memo.content
    existing_memo.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(existing_memo)
    return existing_memo

async def delete_calendar_memo(db: AsyncSession, memo_id: int, user_id: int) -> None:
    result = await db.execute(
        select(main_models.CalendarMemo).where(
            main_models.CalendarMemo.id == memo_id, main_models.CalendarMemo.user_id == user_id
        )
    )
    existing_memo = result.scalar_one_or_none()

    if existing_memo is None:
        raise ValueError(f"CalendarMemo with id {memo_id} not found.")

    await db.delete(existing_memo)
    await db.commit()


async def get_diary_entries(db: AsyncSession, user_id: int) -> list[main_schemas.DiaryEntrySchema]:
    result = await db.execute(
        select(main_models.DiaryEntry)
        .where(main_models.DiaryEntry.user_id == user_id)
        .order_by(main_models.DiaryEntry.entry_date.desc(), main_models.DiaryEntry.created_at.desc())
    )
    return result.scalars().all()


async def get_diary_entries_by_date(db: AsyncSession, entry_date: date, user_id: int) -> list[main_schemas.DiaryEntrySchema]:
    result = await db.execute(
        select(main_models.DiaryEntry)
        .where(main_models.DiaryEntry.entry_date == entry_date, main_models.DiaryEntry.user_id == user_id)
        .order_by(main_models.DiaryEntry.created_at.desc())
    )
    return result.scalars().all()


async def create_diary_entry(
    db: AsyncSession, entry: main_schemas.DiaryEntryCreateSchema, user_id: int
) -> main_schemas.DiaryEntrySchema:
    new_entry = main_models.DiaryEntry(
        entry_date=entry.entry_date,
        title=entry.title,
        content=entry.content,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        user_id=user_id,
    )
    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)
    return new_entry


async def update_diary_entry(
    db: AsyncSession, entry: main_schemas.DiaryEntryUpdateSchema, user_id: int
) -> main_schemas.DiaryEntrySchema:
    result = await db.execute(
        select(main_models.DiaryEntry).where(
            main_models.DiaryEntry.id == entry.id, main_models.DiaryEntry.user_id == user_id
        )
    )
    existing_entry = result.scalar_one_or_none()

    if existing_entry is None:
        raise ValueError(f"DiaryEntry with id {entry.id} not found.")

    existing_entry.entry_date = entry.entry_date
    existing_entry.title = entry.title
    existing_entry.content = entry.content
    existing_entry.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(existing_entry)
    return existing_entry


async def delete_diary_entry(db: AsyncSession, entry_id: int, user_id: int) -> None:
    result = await db.execute(
        select(main_models.DiaryEntry).where(
            main_models.DiaryEntry.id == entry_id, main_models.DiaryEntry.user_id == user_id
        )
    )
    existing_entry = result.scalar_one_or_none()

    if existing_entry is None:
        raise ValueError(f"DiaryEntry with id {entry_id} not found.")

    await db.delete(existing_entry)
    await db.commit()


async def get_calendar_month_summary(
    db: AsyncSession, year: int, month: int, user_id: int
) -> main_schemas.CalendarMonthSummarySchema:
    last_day = monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, last_day)

    result = await db.execute(
        select(main_models.DiaryEntry)
        .where(main_models.DiaryEntry.entry_date >= start)
        .where(main_models.DiaryEntry.entry_date <= end)
        .where(main_models.DiaryEntry.user_id == user_id)
        .order_by(main_models.DiaryEntry.entry_date.asc(), main_models.DiaryEntry.created_at.asc())
    )
    entries = result.scalars().all()

    grouped: dict[date, list[main_models.DiaryEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.entry_date].append(entry)

    days = []
    for day in range(1, last_day + 1):
        current_date = date(year, month, day)
        day_entries = grouped.get(current_date, [])
        days.append(
            main_schemas.CalendarDaySummarySchema(
                entry_date=current_date,
                entry_count=len(day_entries),
                titles=[entry.title for entry in day_entries],
                entries=[
                    main_schemas.DiaryEntrySummarySchema(id=entry.id, title=entry.title, content=entry.content)
                    for entry in day_entries
                ],
            )
        )

    return main_schemas.CalendarMonthSummarySchema(year=year, month=month, days=days)

async def get_user_by_username(
    db: AsyncSession,
    username: str,
) -> main_models.User | None:
    result = await db.execute(
        select(main_models.User).where(main_models.User.username == username)
    )
    return result.scalars().first()

async def post_user(
    db: AsyncSession,
    user: main_models.User
):
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
