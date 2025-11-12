#отвечает за основной FastAPI-приложение - инициализация app, создание таблиц в БД,
#определение всех эндпоинтов (роутов) и интеграция с моделями, схемами, CRUD и аутентификацией

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from database import engine, Base
from models import *
from schemas import *
from crud import *
from auth import *
from dependencies import get_db
from signature import verify_signature

app = FastAPI(title="Event Booking System")  #Инициализация FastAPI-приложения с заголовком
Base.metadata.create_all(bind=engine)  #Создание всех таблиц в БД на основе моделей

#==================== АУТЕНТИФИКАЦИЯ ====================
@app.post("/auth/register", response_model=UserResponse)  #Эндпоинт для регистрации пользователя
def register(user: UserCreate, db: Session = Depends(get_db)):  #Функция: принимает данные пользователя и сессию БД
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    created_user = create_user(db, user)  #Создание и возврат пользователя (теперь включает api_key)
    return created_user

@app.post("/auth/login", response_model=Token)  #Эндпоинт для входа пользователя
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):  #Функция: принимает форму входа и сессию БД
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user.username})  #Создание JWT-токена
    return {"access_token": token, "token_type": "bearer"}  #Возврат токена

@app.post("/auth/logout")  #Эндпоинт для выхода (logout) 
def logout(token: str = Depends(oauth2_scheme)):  #Функция: извлекает токен из headers
    revoked_tokens.add(token)
    return {"message": "Logout successful"}

#==================== ПОЛЬЗОВАТЕЛИ ====================
@app.get("/users/me", response_model=UserResponse)  #Эндпоинт для получения данных текущего пользователя
def read_me(current_user: User = Depends(verify_signature)):  #Функция: зависит от верифицированной подписи
    return current_user

@app.get("/users", response_model=List[UserResponse])  #Эндпоинт для получения списка всех пользователей
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):  #Функция: принимает пагинацию и сессию БД
    return get_users(db, skip, limit)

@app.get("/users/{user_id}", response_model=UserResponse)  #Эндпоинт для получения пользователя по ID
def get_user_detail(user_id: int, db: Session = Depends(get_db)):  #Функция: принимает ID и сессию БД
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.patch("/users/{user_id}", response_model=UserResponse)  #Эндпоинт для обновления пользователя
def update_user_endpoint(user_id: int, data: UserUpdate, db: Session = Depends(get_db),
                         current_user: User = Depends(verify_signature)):  #Функция: принимает ID, данные, сессию, верифицированного пользователя
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    updated = update_user(db, user_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@app.delete("/users/{user_id}", response_model=UserResponse)  #Эндпоинт для удаления пользователя
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(verify_signature)):  #Функция: принимает ID, сессию, верифицированного пользователя
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    deleted = delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted

#==================== КАТЕГОРИИ ====================
@app.post("/categories", response_model=CategoryResponse)  #Эндпоинт для создания категории
def create_category(cat: CategoryCreate, db: Session = Depends(get_db),  #Функция: принимает данные категории, сессию БД
                    current_user: User = Depends(verify_signature)):
    return create_category(db, cat)

@app.get("/categories", response_model=List[CategoryResponse])  #Эндпоинт для получения списка категорий
def list_categories(db: Session = Depends(get_db)):  #Функция: принимает сессию БД
    return get_categories(db)

#==================== СОБЫТИЯ ====================
@app.post("/events", response_model=EventResponse)  #Эндпоинт для создания события
def create_event(event: EventCreate, db: Session = Depends(get_db),  #Функция: принимает данные события, сессию БД
                 current_user: User = Depends(verify_signature)):
    return create_event(db, event, owner_id=current_user.id)

@app.get("/events", response_model=List[EventResponse])  #Эндпоинт для получения списка событий
def list_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):  #Функция: принимает параметры пагинации и сессию БД
    return get_events(db, skip, limit)

@app.get("/events/{event_id}", response_model=EventResponse)  #Эндпоинт для получения события по ID
def get_event_detail(event_id: int, db: Session = Depends(get_db)):  #Функция: принимает ID и сессию БД
    ev = get_event(db, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    return ev

@app.patch("/events/{event_id}", response_model=EventResponse)  #Эндпоинт для обновления события
def update_event(event_id: int, data: dict, db: Session = Depends(get_db),  #Функция: принимает ID, данные, сессию БД
                 current_user: User = Depends(verify_signature)):
    ev = get_event(db, event_id)
    if not ev or ev.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    updated = update_event(db, event_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated

@app.delete("/events/{event_id}", response_model=EventResponse)  #Эндпоинт для удаления события
def delete_event_endpoint(event_id: int, db: Session = Depends(get_db),  #Функция: принимает ID, сессию БД
                          current_user: User = Depends(verify_signature)):
    ev = get_event(db, event_id)
    if not ev or ev.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    deleted = delete_event(db, event_id)
    return deleted

#==================== БРОНИРОВАНИЯ ====================
@app.post("/bookings", response_model=BookingResponse)  #Эндпоинт для создания бронирования
def book_event(booking: BookingCreate, db: Session = Depends(get_db),  #Функция: принимает данные бронирования, сессию БД
               current_user: User = Depends(verify_signature)):
    created = create_booking(db, booking, user_id=current_user.id)
    if not created:
        raise HTTPException(status_code=400, detail="Not enough seats or event not found")
    return created

@app.get("/bookings/me", response_model=List[BookingResponse])  #Эндпоинт для получения бронирований пользователя
def my_bookings(db: Session = Depends(get_db), current_user: User = Depends(verify_signature)):  #Функция: принимает сессию БД и верифицированного пользователя
    return get_user_bookings(db, current_user.id)

@app.get("/bookings/{booking_id}", response_model=BookingResponse)  #Эндпоинт для получения бронирования по ID
def get_booking_detail(booking_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(verify_signature)):  #Функция: принимает ID, сессию, верифицированного пользователя
    booking = get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return booking

@app.patch("/bookings/{booking_id}", response_model=BookingResponse)  #Эндпоинт для обновления бронирования
def update_booking_endpoint(booking_id: int, data: dict, db: Session = Depends(get_db),
                            current_user: User = Depends(verify_signature)):  #Функция: принимает ID, данные, сессию, пользователя
    updated = update_booking(db, booking_id, data, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Booking not found or not authorized")
    return updated

@app.delete("/bookings/{booking_id}", response_model=BookingResponse)  #Эндпоинт для отмены бронирования
def cancel_booking_endpoint(booking_id: int, db: Session = Depends(get_db),  #Функция: принимает ID, сессию БД
                            current_user: User = Depends(verify_signature)):
    cancelled = cancel_booking(db, booking_id, current_user.id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Booking not found")
    return cancelled

#==================== ОТЗЫВЫ ====================
@app.post("/reviews", response_model=ReviewResponse)  #Эндпоинт для добавления отзыва
def add_review(review: ReviewCreate, db: Session = Depends(get_db),  #Функция: принимает данные отзыва, сессию БД
               current_user: User = Depends(verify_signature)):
    return create_review(db, review, user_id=current_user.id)

@app.get("/reviews/event/{event_id}", response_model=List[ReviewResponse])  #Эндпоинт для получения отзывов по событию
def event_reviews(event_id: int, db: Session = Depends(get_db)):  #Функция: принимает ID события и сессию БД
    return get_reviews_by_event(db, event_id)

@app.patch("/reviews/{review_id}", response_model=ReviewResponse)  #Эндпоинт для обновления отзыва
def update_review_endpoint(review_id: int, data: dict, db: Session = Depends(get_db),
                           current_user: User = Depends(verify_signature)):  #Функция: принимает ID, данные, сессию, пользователя
    updated = update_review(db, review_id, data, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Review not found or not authorized")
    return updated

@app.delete("/reviews/{review_id}", response_model=ReviewResponse)  #Эндпоинт для удаления отзыва
def delete_review_endpoint(review_id: int, db: Session = Depends(get_db),
                           current_user: User = Depends(verify_signature)):  #Функция: принимает ID, сессию, пользователя
    deleted = delete_review(db, review_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found or not authorized")
    return deleted

#==================== ПОИСК (доп.) ====================
@app.get("/events/search", response_model=List[EventResponse])  #Эндпоинт для поиска событий
def search_events(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):  #Функция: принимает запрос поиска и сессию БД
    return db.query(Event).filter(Event.title.contains(q)).all()