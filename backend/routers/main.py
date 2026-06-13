from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
import db
from typing import Annotated
from shcemas.main import (
    HabitCreateSchema,
    HabitDeleteSchema,
    HabitResponseSchema,
    HabitSchema,
    HabitUpdateSchema,
)
import cruds.main as habit_cruds
import models.main as habit_models

router = APIRouter(tags=["habits"])

@router.get("/habits", response_model=list[HabitSchema])
async def get_habits(db: Annotated[AsyncSession, Depends(db.get_dbsession)]):
    return await habit_cruds.get_habits(db)

@router.get("/habits/{category}", response_model=list[HabitSchema])
async def get_habit_by_category(category: str, db: Annotated[AsyncSession, Depends(db.get_dbsession)]):
    try:
        return await habit_cruds.get_habit_by_category(db, category)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/habits", response_model=HabitSchema, status_code=status.HTTP_201_CREATED)
async def create_habit(habit: HabitCreateSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)]):
    return await habit_cruds.create_habit(db, habit)

@router.delete("/habits", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(habit: HabitDeleteSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)]):
    await habit_cruds.delete_habit(db, habit.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/habits", response_model=HabitSchema)
async def update_habit(habit: HabitUpdateSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)]):
    return await habit_cruds.update_habit(db, habit)
