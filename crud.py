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
    role = user.role if user.role in ("admin", "user") else "user"
    db_user = User(username=user.username, password=hashed, api_key=api_key, role=role)
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
    if data.role in ("admin", "user"):
        db_user.role = data.role
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
def create_category(db: Session, cat: CategoryCreate):
    db_cat = Category(**cat.dict())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

def get_categories(db: Session):
    return db.query(Category).all()

def get_category_by_name(db: Session, name: str):
    return db.query(Category).filter(Category.name == name).first()

def get_category(db: Session, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()

def delete_category(db: Session, category_id: int):
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    db.delete(db_category)
    db.commit()
    return db_category

#---------- EVENT ----------
def create_event(db: Session, event: EventCreate, owner_id: int):
    from crud import get_category_by_name
    cat = get_category_by_name(db, event.category_name)
    if not cat:
        return None
    data = event.dict()
    data.pop('category_name')
    data['category_id'] = cat.id
    db_event = Event(**data, owner_id=owner_id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_event(db: Session, event_id: int):  #Функция для получения события по ID
    return db.query(Event).filter(Event.id == event_id).first()

def get_events(db: Session, skip: int = 0, limit: int = 100):  #Функция для получения списка событий с пагинацией
    return db.query(Event).offset(skip).limit(limit).all()

def update_event(db: Session, event_id: int, data: dict):
    db_event = get_event(db, event_id)
    if not db_event:
        return None
    # Обработка category_name
    if 'category_name' in data:
        from crud import get_category_by_name
        cat = get_category_by_name(db, data['category_name'])
        if not cat:
            return None
        data['category_id'] = cat.id
        data.pop('category_name')
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
    from datetime import datetime
    event = get_event(db, booking.event_id)
    if not event:
        return None
    # Проверка: событие не должно быть в прошлом
    if event.date <= datetime.utcnow():
        return None
    # Проверка: достаточно мест
    if event.seats < booking.seats:
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

def update_booking(db: Session, booking_id: int, data: dict, user_id: int, allow_admin: bool = False):  #Функция для обновления бронирования
    db_booking = get_booking(db, booking_id)
    if not db_booking:
        return None
    if not allow_admin and db_booking.user_id != user_id:
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

def cancel_booking(db: Session, booking_id: int, user_id: int, allow_admin: bool = False):  #Функция для отмены бронирования
    query = db.query(Booking).filter(Booking.id == booking_id)
    if not allow_admin:
        query = query.filter(Booking.user_id == user_id)
    booking = query.first()
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
    from datetime import datetime
    from models import Booking
    
    # Проверка: пользователь должен иметь бронирование на это событие
    booking = db.query(Booking).filter(
        Booking.user_id == user_id,
        Booking.event_id == review.event_id
    ).first()
    if not booking:
        return None  # Нет бронирования
    
    # Проверка: событие должно быть в прошлом
    event = get_event(db, review.event_id)
    if not event:
        return None
    if event.date > datetime.utcnow():
        return None  # Событие еще не прошло
    
    # Проверка: у пользователя не должно быть уже отзыва на это событие
    existing_review = db.query(Review).filter(
        Review.user_id == user_id,
        Review.event_id == review.event_id
    ).first()
    if existing_review:
        return None  # Отзыв уже существует
    
    db_review = Review(**review.dict(), user_id=user_id, is_edited=0)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def get_review(db: Session, review_id: int):  #Функция для получения отзыва по ID (для внутренних нужд)
    return db.query(Review).filter(Review.id == review_id).first()

def get_reviews_by_event(db: Session, event_id: int):  #Функция для получения отзывов по событию
    return db.query(Review).filter(Review.event_id == event_id).all()

def update_review(db: Session, review_id: int, data: dict, user_id: int, allow_admin: bool = False):  #Функция для обновления отзыва
    db_review = get_review(db, review_id)
    if not db_review:
        return None
    # Админ не может редактировать чужие отзывы, только свои
    # Обычный пользователь может редактировать только свои отзывы
    if db_review.user_id != user_id:
        return None
    for k, v in data.items():
        if hasattr(db_review, k):
            setattr(db_review, k, v)
    # Помечаем отзыв как измененный
    db_review.is_edited = 1
    db.commit()
    db.refresh(db_review)
    return db_review

def delete_review(db: Session, review_id: int, user_id: int, allow_admin: bool = False):  #Функция для удаления отзыва
    db_review = get_review(db, review_id)
    if not db_review:
        return None
    if not allow_admin and db_review.user_id != user_id:
        return None
    db.delete(db_review)
    db.commit()
    return db_review