import os
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select, func

Base = declarative_base()

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'habit_maker.db')
DATABASE_URL = f'sqlite+aiosqlite:///{DB_PATH}'

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_dbsession():
    async with async_session() as session:
        yield session

async def init_db(*, seed_sample: bool, reset: bool) -> None:
    import models.main as models_main

    async with engine.begin() as conn:
        if reset:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        if not seed_sample:
            return

        from models.main import Habit
        import cruds.main as habit_cruds
        from auth import get_password_hash

        async with async_session() as session:
            # Fixed demo account for seeded data: username=demo / password=demopassword
            demo_user = await habit_cruds.get_user_by_username(session, "demo")
            if demo_user is None:
                demo_user = await habit_cruds.post_user(
                    session,
                    models_main.User(
                        username="demo",
                        password_hash=get_password_hash("demopassword"),
                    ),
                )
            demo_user_id = demo_user.id

            mail_count = await session.scalar(select(func.count(Habit.id)))
            diary_count = await session.scalar(select(func.count(models_main.DiaryEntry.id)))

            to_add = []

            if (mail_count or 0) == 0:
                to_add.extend(_sample_habits(demo_user_id))

            if (diary_count or 0) == 0:
                to_add.extend(_sample_diary_entries(demo_user_id))

            if to_add:
                session.add_all(to_add)
                await session.commit()

def _sample_habits(user_id: int):
    from models.main import Habit
    return [
        Habit(name="Morning Exercise", description="Engage in physical activity for at least 30 minutes every morning.", category="Health", user_id=user_id),
        Habit(name="Reading", description="Read a book or an article for at least 20 minutes daily.", category="Personal Development", user_id=user_id),
        Habit(name="Meditation", description="Practice mindfulness meditation for 10 minutes each day.", category="Mental Health", user_id=user_id),
        Habit(name="Healthy Eating", description="Consume at least 5 servings of fruits and vegetables daily.", category="Health", user_id=user_id),
        Habit(name="Gratitude Journal", description="Write down three things you are grateful for every evening.", category="Mental Health", user_id=user_id),
        Habit(name="Weekly Planning", description="Review the week and plan the top priorities.", category="My Habits", user_id=user_id),
    ]


def _sample_diary_entries(user_id: int):
    from datetime import date
    from models.main import DiaryEntry

    return [
        DiaryEntry(
            entry_date=date(2026, 6, 1),
            title="Start of the month",
            content="Began setting up the habit tracker and diary workflow.",
            user_id=user_id,
        ),
        DiaryEntry(
            entry_date=date(2026, 6, 15),
            title="Backend diary API",
            content="Added diary entry CRUD endpoints and monthly calendar summaries.",
            user_id=user_id,
        ),
    ]

