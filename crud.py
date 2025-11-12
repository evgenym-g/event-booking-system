#CRUD-операции (Create, Read, Update, Delete) над сущностями базы данных - пользователи, категории, события, бронирования и отзывы
#функции для взаимодействия с БД через SQLAlchemy

from sqlalchemy.orm import Session  #для работы с сессиями БД.
from models import User, Event, Booking, Review, Category
from schemas import *
from passlib.context import CryptContext  #для хэширования паролей.
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#---------- USER ----------
def get_user(db: Session, user_id: int):  #Функция для получения пользователя по ID
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):  #Функция для получения пользователя по username
    return db.query(User).filter(User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):  #Функция для получения списка всех пользователей с пагинацией
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):  #Функция для создания нового пользователя
    hashed = pwd_context.hash(user.password)
    api_key = secrets.token_hex(32)
    db_user = User(username=user.username, password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, data: UserUpdate):  #Функция для обновления пользователя
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    if data.username:
        db_user.username = data.username
    if data.password:
        db_user.password = pwd_context.hash(data.password)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):  #Функция для удаления пользователя
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

#---------- CATEGORY ----------
def create_category(db: Session, cat: CategoryCreate):  #Функция для создания новой категории
    db_cat = Category(**cat.dict())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

def get_categories(db: Session):  #Функция для получения всех категорий
    return db.query(Category).all()

#---------- EVENT ----------
def create_event(db: Session, event: EventCreate, owner_id: int):  #Функция для создания нового события
    db_event = Event(**event.dict(), owner_id=owner_id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_event(db: Session, event_id: int):  #Функция для получения события по ID
    return db.query(Event).filter(Event.id == event_id).first()

def get_events(db: Session, skip: int = 0, limit: int = 100):  #Функция для получения списка событий с пагинацией
    return db.query(Event).offset(skip).limit(limit).all()

def update_event(db: Session, event_id: int, data: dict):  #Функция для обновления события
    db_event = get_event(db, event_id)
    if not db_event:
        return None
    for k, v in data.items():
        if hasattr(db_event, k):
            setattr(db_event, k, v)
    db.commit()
    db.refresh(db_event)
    return db_event

def delete_event(db: Session, event_id: int):  #Функция для удаления события
    db_event = get_event(db, event_id)
    if db_event:
        db.delete(db_event)
        db.commit()
    return db_event

#---------- BOOKING ----------
def create_booking(db: Session, booking: BookingCreate, user_id: int):  #Функция для создания бронирования
    event = get_event(db, booking.event_id)
    if not event or event.seats < booking.seats:
        return None
    db_booking = Booking(**booking.dict(), user_id=user_id)
    event.seats -= booking.seats
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_booking(db: Session, booking_id: int):  #Функция для получения бронирования по ID
    return db.query(Booking).filter(Booking.id == booking_id).first()

def get_user_bookings(db: Session, user_id: int):  #Функция для получения бронирований пользователя
    return db.query(Booking).filter(Booking.user_id == user_id).all()

def update_booking(db: Session, booking_id: int, data: dict, user_id: int):  #Функция для обновления бронирования
    db_booking = get_booking(db, booking_id)
    if not db_booking or db_booking.user_id != user_id:
        return None
    event = get_event(db, db_booking.event_id)
    if 'seats' in data:
        new_seats = data['seats']
        if new_seats > db_booking.seats:
            if event.seats < (new_seats - db_booking.seats):
                return None
            event.seats -= (new_seats - db_booking.seats)
        elif new_seats < db_booking.seats:
            event.seats += (db_booking.seats - new_seats)
        db_booking.seats = new_seats
    db.commit()
    db.refresh(db_booking)
    return db_booking

def cancel_booking(db: Session, booking_id: int, user_id: int):  #Функция для отмены бронирования
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == user_id).first()
    if not booking:
        return None
    event = get_event(db, booking.event_id)
    if event:
        event.seats += booking.seats
    db.delete(booking)
    db.commit()
    return booking

#---------- REVIEW ----------
def create_review(db: Session, review: ReviewCreate, user_id: int):  #Функция для создания отзыва
    db_review = Review(**review.dict(), user_id=user_id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def get_review(db: Session, review_id: int):  #Функция для получения отзыва по ID (для внутренних нужд)
    return db.query(Review).filter(Review.id == review_id).first()

def get_reviews_by_event(db: Session, event_id: int):  #Функция для получения отзывов по событию
    return db.query(Review).filter(Review.event_id == event_id).all()

def update_review(db: Session, review_id: int, data: dict, user_id: int):  #Функция для обновления отзыва
    db_review = get_review(db, review_id)
    if not db_review or db_review.user_id != user_id:
        return None
    for k, v in data.items():
        if hasattr(db_review, k):
            setattr(db_review, k, v)
    db.commit()
    db.refresh(db_review)
    return db_review

def delete_review(db: Session, review_id: int, user_id: int):  #Функция для удаления отзыва
    db_review = get_review(db, review_id)
    if not db_review or db_review.user_id != user_id:
        return None
    db.delete(db_review)
    db.commit()
    return db_review