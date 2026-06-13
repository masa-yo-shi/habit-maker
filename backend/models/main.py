from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

class Habit(Base):
    __tablename__ = 'habits'

    id = Column(Integer, primary_key=True, index=True)
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