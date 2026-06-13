from pydantic import BaseModel, Field

try:
    from pydantic import ConficgDict
except ImportError:
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
