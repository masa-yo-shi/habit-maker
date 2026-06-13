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
    import models.main

    async with engine.begin() as conn:
        if reset:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        if not seed_sample:
            return
        
        from models.main import Habit

        async with async_session() as session:
            mail_count = await session.scalar(select(func.count(Habit.id)))

            to_add = []

            if (mail_count or 0) == 0:
                to_add.extend(_sample_habits())
            
            if to_add:
                session.add_all(to_add)
                await session.commit()

def _sample_habits():
    from models.main import Habit
    return [
        Habit(name="Morning Exercise", description="Engage in physical activity for at least 30 minutes every morning.", category="Health"),
        Habit(name="Reading", description="Read a book or an article for at least 20 minutes daily.", category="Personal Development"),
        Habit(name="Meditation", description="Practice mindfulness meditation for 10 minutes each day.", category="Mental Health"),
        Habit(name="Healthy Eating", description="Consume at least 5 servings of fruits and vegetables daily.", category="Health"),
        Habit(name="Gratitude Journal", description="Write down three things you are grateful for every evening.", category="Mental Health"),
    ]
    

