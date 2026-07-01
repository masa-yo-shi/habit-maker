from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime, timezone

class Habit(Base):
    __tablename__ = 'habits'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String, index=True)
    description = Column(String)
    category = Column(String)
    response = relationship("HabitResponse", back_populates="habit", uselist=False)

class HabitResponse(Base):
    __tablename__ = 'habit_responses'

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey('habits.id'), unique=True, nullable=False)
    response_title = Column(String,nullable=False)
    response_description = Column(String, nullable=False)
    habit = relationship("Habit", back_populates="response", uselist=False)


class CalendarMemo(Base):
    __tablename__ = 'calendar_memos'
    __table_args__ = (
        UniqueConstraint('user_id', 'memo_date', name='uq_calendar_memo_user_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    memo_date = Column(Date, index=True, nullable=False)
    content = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DiaryEntry(Base):
    __tablename__ = 'diary_entries'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    entry_date = Column(Date, index=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
