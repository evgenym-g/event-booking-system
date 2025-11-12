#отвечает за определение Pydantic-схем для валидации входных и выходных данных API
#Схемы используются для сериализации/десериализации и валидации

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):  #Схема для создания пользователя (входные данные)
    username: str
    password: str

class UserUpdate(BaseModel):  #Схема для обновления пользователя (частичные данные)
    username: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel):  #Схема для ответа с данными пользователя
    id: int
    username: str
    api_key: str  # Новый: возвращаем api_key клиенту (только при регистрации/login если нужно)

    class Config:  #Конфигурация схемы
        from_attributes = True  #Разрешение создания из атрибутов ORM-моделей

class CategoryCreate(BaseModel):  #Схема для создания категории
    name: str

class CategoryResponse(BaseModel):  #Схема для ответа с данными категории
    id: int
    name: str

    class Config:  #Конфигурация схемы
        from_attributes = True  #Разрешение создания из атрибутов ORM-моделей

class EventCreate(BaseModel):  #Схема для создания события
    title: str
    date: datetime
    seats: int
    category_id: int

class EventResponse(BaseModel):  #Схема для ответа с данными события
    id: int
    title: str
    date: datetime
    seats: int
    category_id: int
    owner_id: int

    class Config:  #Конфигурация схемы
        from_attributes = True  #Разрешение создания из атрибутов ORM-моделей

class BookingCreate(BaseModel):  #Схема для создания бронирования
    event_id: int
    seats: int

class BookingResponse(BaseModel):  #Схема для ответа с данными бронирования
    id: int
    seats: int
    user_id: int
    event_id: int

    class Config:  #Конфигурация схемы
        from_attributes = True  #Разрешение создания из атрибутов ORM-моделей

class ReviewCreate(BaseModel):  #Схема для создания отзыва
    event_id: int
    text: str
    rating: float

class ReviewResponse(BaseModel):  #Схема для ответа с данными отзыва
    id: int
    text: str
    rating: float
    user_id: int
    event_id: int

    class Config:  #Конфигурация схемы
        from_attributes = True  #Разрешение создания из атрибутов ORM-моделей

class Token(BaseModel):  #Схема для токена аутентификации
    access_token: str
    token_type: str