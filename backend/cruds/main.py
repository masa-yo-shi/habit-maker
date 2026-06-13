from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import shcemas.main as main_schemas
import models.main as main_models

async def get_habits(db: AsyncSession) -> list[main_schemas.HabitSchema]:
    result = await db.execute(select(main_models.Habit))
    habits = result.scalars().all()
    return habits

async def get_habit_by_category(db: AsyncSession, category: str) -> list[main_schemas.HabitSchema]:
    if category not in ["Health", "Personal Development", "Mental Health"]:
        raise ValueError("Invalid category. Must be one of: 'Health', 'Personal Development', 'Mental Health'.")
    result = await db.execute(select(main_models.Habit).where(main_models.Habit.category == category))
    habits = result.scalars().all()
    return habits

async def create_habit(db: AsyncSession, habit: main_schemas.HabitCreateSchema) -> main_schemas.HabitSchema:
    new_habit = main_models.Habit(name=habit.name, description=habit.description, category=habit.category)
    db.add(new_habit)
    await db.commit()
    await db.refresh(new_habit)
    return new_habit

async def update_habit(db: AsyncSession, habit: main_schemas.HabitUpdateSchema) -> main_schemas.HabitSchema:
    result = await db.execute(select(main_models.Habit).where(main_models.Habit.id == habit.id))
    existing_habit = result.scalar_one_or_none()
    
    if existing_habit is None:
        raise ValueError(f"Habit with id {habit.id} not found.")
    
    existing_habit.name = habit.name
    existing_habit.description = habit.description
    existing_habit.category = habit.category
    
    await db.commit()
    await db.refresh(existing_habit)
    return existing_habit

async def delete_habit(db: AsyncSession, habit_id: int) -> None:
    result = await db.execute(select(main_models.Habit).where(main_models.Habit.id == habit_id))
    existing_habit = result.scalar_one_or_none()
    
    if existing_habit is None:
        raise ValueError(f"Habit with id {habit_id} not found.")
    
    await db.delete(existing_habit)
    await db.commit()