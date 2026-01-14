#отвечает за определение моделей базы данных с использованием SQLAlchemy 
#Каждая модель представляет таблицу в БД и определяет её структуру, поля и связи

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float  #Идля определения полей таблиц
from sqlalchemy.orm import relationship  #для определения связей между моделями
from database import Base  #Импорт базового класса Base из database.py
import secrets  #генерация api_key

class User(Base):  #Модель пользователя
    __tablename__ = "users"  #Название таблицы в БД
    id = Column(Integer, primary_key=True, index=True)  #Поле ID: первичный ключ, целое число, индексировано
    username = Column(String, unique=True, index=True)  #Поле username: строка, уникальное, индексировано
    password = Column(String)  #Поле password: строка для хранения хэшированного пароля
    api_key = Column(String, unique=True)  # Новое поле: API-ключ для HMAC
    role = Column(String, default="user")  # Роль: "admin" или "user"

    events = relationship("Event", back_populates="owner")  #Связь: события, принадлежащие пользователю (one-to-many)
    bookings = relationship("Booking", back_populates="user")  #Связь: бронирования пользователя (one-to-many)
    reviews = relationship("Review", back_populates="user")  #Связь: отзывы пользователя (one-to-many)

class Category(Base):  #Модель категории
    __tablename__ = "categories"  #Название таблицы в БД
    id = Column(Integer, primary_key=True, index=True)  #Поле ID: первичный ключ, целое число, индексировано
    name = Column(String, index=True)  #Поле name: строка, индексировано

    events = relationship("Event", back_populates="category")  #Связь: события в категории (one-to-many)

class Event(Base):  #Модель события
    __tablename__ = "events"  #Название таблицы в БД
    id = Column(Integer, primary_key=True, index=True)  #Поле ID: первичный ключ, целое число, индексировано
    title = Column(String, index=True)  #Поле title: строка, индексировано
    date = Column(DateTime)  #Поле date: дата и время
    seats = Column(Integer)  #Поле seats: целое число для количества мест
    category_id = Column(Integer, ForeignKey("categories.id"))  #Поле category_id: внешний ключ на категории
    owner_id = Column(Integer, ForeignKey("users.id"))  #Поле owner_id: внешний ключ на пользователя-владельца

    category = relationship("Category", back_populates="events")  #Связь: категория события (many-to-one)
    owner = relationship("User", back_populates="events")  #Связь: владелец события (many-to-one)
    bookings = relationship("Booking", back_populates="event")  #Связь: бронирования на событие (one-to-many)
    reviews = relationship("Review", back_populates="event")  #Связь: отзывы на событие (one-to-many)

class Booking(Base):  #Модель бронирования
    __tablename__ = "bookings"  #Название таблицы в БД
    id = Column(Integer, primary_key=True, index=True)  #Поле ID: первичный ключ, целое число, индексировано
    seats = Column(Integer)  #Поле seats: целое число для количества забронированных мест
    user_id = Column(Integer, ForeignKey("users.id"))  #Поле user_id: внешний ключ на пользователя
    event_id = Column(Integer, ForeignKey("events.id"))  #Поле event_id: внешний ключ на событие

    user = relationship("User", back_populates="bookings")  #Связь: пользователь бронирования (many-to-one)
    event = relationship("Event", back_populates="bookings")  #Связь: событие бронирования (many-to-one)

class Review(Base):  #Модель отзыва
    __tablename__ = "reviews"  #Название таблицы в БД
    id = Column(Integer, primary_key=True, index=True)  #Поле ID: первичный ключ, целое число, индексировано
    text = Column(String)  #Поле text: строка для текста отзыва
    rating = Column(Float)  #Поле rating: вещественное число для рейтинга
    user_id = Column(Integer, ForeignKey("users.id"))  #Поле user_id: внешний ключ на пользователя
    event_id = Column(Integer, ForeignKey("events.id"))  #Поле event_id: внешний ключ на событие
    is_edited = Column(Integer, default=0)  #Поле is_edited: 0 - не изменен, 1 - изменен

    user = relationship("User", back_populates="reviews")  #Связь: пользователь отзыва (many-to-one)
    event = relationship("Event", back_populates="reviews")  #Связь: событие отзыва (many-to-one)