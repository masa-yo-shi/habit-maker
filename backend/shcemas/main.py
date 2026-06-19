from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - pydantic v1 fallback
    ConfigDict = None

class HabitSchema(BaseModel):
    id: int = Field(..., description="id of the habit")
    name: str = Field(..., description="name of the habit")
    description: str = Field(..., description="description of the habit")
    category: str = Field(..., description="category of the habit")
    
    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

class HabitResponseSchema(BaseModel):
    id: int = Field(..., description="id of the habit response")
    response_title: str = Field(..., description="title of the habit response")
    response_description: str = Field(..., description="description of the habit response")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

class HabitCreateSchema(BaseModel):
    name: str = Field(..., description="name of the habit")
    description: str = Field(..., description="description of the habit")
    category: str = Field(..., description="category of the habit")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

class HabitUpdateSchema(BaseModel):
    id: int = Field(..., description="id of the habit")
    name: str = Field(..., description="name of the habit")
    description: str = Field(..., description="description of the habit")
    category: str = Field(..., description="category of the habit")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True
        
class HabitDeleteSchema(BaseModel):
    id: int = Field(..., description="id of the habit")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class CalendarMemoSchema(BaseModel):
    id: int = Field(..., description="id of the calendar memo")
    memo_date: date = Field(..., description="date of the memo")
    content: str = Field(..., description="memo content")
    updated_at: datetime = Field(..., description="last updated at")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class CalendarMemoCreateSchema(BaseModel):
    memo_date: date = Field(..., description="date of the memo")
    content: str = Field(..., description="memo content")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class CalendarMemoUpdateSchema(BaseModel):
    id: int = Field(..., description="id of the calendar memo")
    memo_date: date = Field(..., description="date of the memo")
    content: str = Field(..., description="memo content")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class CalendarMemoDeleteSchema(BaseModel):
    id: int = Field(..., description="id of the calendar memo")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class DiaryEntrySchema(BaseModel):
    id: int = Field(..., description="id of the diary entry")
    entry_date: date = Field(..., description="date of the diary entry")
    title: str = Field(..., description="title of the diary entry")
    content: str = Field(..., description="content of the diary entry")
    created_at: datetime = Field(..., description="created at")
    updated_at: datetime = Field(..., description="updated at")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class DiaryEntryCreateSchema(BaseModel):
    entry_date: date = Field(..., description="date of the diary entry")
    title: str = Field(..., description="title of the diary entry")
    content: str = Field(..., description="content of the diary entry")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class DiaryEntryUpdateSchema(BaseModel):
    id: int = Field(..., description="id of the diary entry")
    entry_date: date = Field(..., description="date of the diary entry")
    title: str = Field(..., description="title of the diary entry")
    content: str = Field(..., description="content of the diary entry")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class DiaryEntryDeleteSchema(BaseModel):
    id: int = Field(..., description="id of the diary entry")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class CalendarDaySummarySchema(BaseModel):
    entry_date: date = Field(..., description="date in the calendar")
    entry_count: int = Field(..., description="number of diary entries")
    titles: list[str] = Field(default_factory=list, description="titles of diary entries")
    entries: list["DiaryEntrySummarySchema"] = Field(default_factory=list, description="diary entry summaries")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class CalendarMonthSummarySchema(BaseModel):
    year: int = Field(..., description="year of the calendar summary")
    month: int = Field(..., description="month of the calendar summary")
    days: list[CalendarDaySummarySchema] = Field(..., description="calendar day summaries")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class Page2RegisterHabitSchema(BaseModel):
    habit_id: int = Field(..., description="habit id to register")
    category: str | None = Field(default=None, description="current category")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class DiaryEntrySummarySchema(BaseModel):
    id: int = Field(..., description="id of the diary entry")
    title: str = Field(..., description="title of the diary entry")
    content: str = Field(..., description="content of the diary entry")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


CalendarDaySummarySchema.model_rebuild()


class TimerStartSchema(BaseModel):
    habit: str = Field(..., description="selected habit name")
    memo: str = Field(default="", description="memo to save with the timer")
    duration_seconds: int = Field(default=300, ge=1, le=86400, description="timer duration in seconds")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class TimerStatusSchema(BaseModel):
    timer_id: str = Field(..., description="timer identifier")
    status: Literal["running", "completed", "failed"] = Field(..., description="timer state")
    habit: str = Field(..., description="selected habit name")
    memo: str = Field(default="", description="memo to save with the timer")
    entry_date: date = Field(..., description="entry date to record")
    duration_seconds: int = Field(..., description="timer duration in seconds")
    started_at: datetime = Field(..., description="when the timer started")
    scheduled_for: datetime = Field(..., description="when the timer should complete")
    remaining_seconds: int = Field(..., description="seconds left until completion")
    diary_entry_id: int | None = Field(default=None, description="created diary entry id")
    error: str | None = Field(default=None, description="timer failure reason")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class UserPublic(BaseModel):
    id: int = Field(..., description="id of the user")
    username: str = Field(..., description="username of the user")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class UserInDB(BaseModel):
    id: int = Field(..., description="id of the user")
    username: str = Field(..., description="username of the user")
    hashed_password: str = Field(..., description="hashed password of the user")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

class ResponseSchema(BaseModel):
    message: str = Field(..., description="response message")

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True