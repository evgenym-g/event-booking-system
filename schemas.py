from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    api_key: str
    role: str

    class Config:
        from_attributes = True

class CategoryCreate(BaseModel):
    name: str

class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class EventCreate(BaseModel):
    title: str
    date: datetime
    seats: int
    category_name: str

class EventResponse(BaseModel):
    id: int
    title: str
    date: datetime
    seats: int
    category_id: int
    owner_id: int

    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    event_id: int
    seats: int

class BookingResponse(BaseModel):
    id: int
    seats: int
    user_id: int
    event_id: Optional[int] = None

    class Config:
        from_attributes = True

class ReviewCreate(BaseModel):
    event_id: int
    text: str
    rating: float

class ReviewResponse(BaseModel):
    id: int
    text: str
    rating: float
    user_id: int
    event_id: int
    is_edited: Optional[int] = 0
    username: Optional[str] = None
    event_title: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
