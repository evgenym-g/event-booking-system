from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from database import engine, Base
from models import *
from schemas import *
from crud import *
from auth import *
from dependencies import get_db
from signature import verify_signature

app = FastAPI(title="Event Booking System")
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_admin(current_user: User = Depends(verify_signature)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user

@app.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    created_user = create_user(db, user)
    return created_user

@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "api_key": user.api_key,
        "role": user.role,
        "username": user.username,
        "user_id": user.id,
    }

@app.post("/auth/logout")
def logout(token: str = Depends(oauth2_scheme)):
    revoked_tokens.add(token)
    return {"message": "Logout successful"}

@app.get("/users/me", response_model=UserResponse)
def read_me(current_user: User = Depends(verify_signature)):
    return current_user

@app.get("/users", response_model=List[UserResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
              current_user: User = Depends(require_admin)):
    return get_users(db, skip, limit)

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user_detail(user_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(verify_signature)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

@app.patch("/users/{user_id}", response_model=UserResponse)
def update_user_endpoint(user_id: int, data: UserUpdate, db: Session = Depends(get_db),
                         current_user: User = Depends(verify_signature)):
    if user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    if data.role and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can change role")
    updated = update_user(db, user_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(verify_signature)):
    if user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    deleted = delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted

@app.post("/categories", response_model=CategoryResponse)
def create_category_endpoint(item: CategoryCreate, db: Session = Depends(get_db),
                    current_user: User = Depends(require_admin)):
    return create_category(db, item)

@app.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return get_categories(db)

@app.delete("/categories/{category_id}", response_model=CategoryResponse)
def delete_category_endpoint(category_id: int, db: Session = Depends(get_db),
                            current_user: User = Depends(require_admin)):
    deleted = delete_category(db, category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    return deleted

@app.post("/events", response_model=EventResponse)
def create_event_endpoint(item: EventCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(verify_signature)):
    result = create_event(db, item, owner_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Category not found")
    return result

@app.get("/events", response_model=List[EventResponse])
def list_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_events(db, skip, limit)

@app.get("/events/{event_id}", response_model=EventResponse)
def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    item = get_event(db, event_id)
    if not item:
        raise HTTPException(status_code=404, detail="Event not found")
    return item

@app.patch("/events/{event_id}", response_model=EventResponse)
def update_event_endpoint(event_id: int, data: dict, db: Session = Depends(get_db),
                 current_user: User = Depends(verify_signature)):
    item = get_event(db, event_id)
    if not item:
        raise HTTPException(status_code=404, detail="Event not found")
    if item.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    if "date" in data and isinstance(data["date"], str):
        try:
            from datetime import datetime
            data["date"] = datetime.fromisoformat(data["date"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            raise HTTPException(status_code=400, detail="Invalid date format")
    updated = update_event(db, event_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found or category not found")
    return updated

@app.delete("/events/{event_id}", response_model=EventResponse)
def delete_event_endpoint(event_id: int, db: Session = Depends(get_db),
                          current_user: User = Depends(verify_signature)):
    item = get_event(db, event_id)
    if not item:
        raise HTTPException(status_code=404, detail="Event not found")
    if item.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    deleted = delete_event(db, event_id)
    return deleted

@app.post("/bookings", response_model=BookingResponse)
def book_event(booking: BookingCreate, db: Session = Depends(get_db),
               current_user: User = Depends(verify_signature)):
    created = create_booking(db, booking, user_id=current_user.id)
    if not created:
        event = get_event(db, booking.event_id)
        if not event:
            raise HTTPException(status_code=400, detail="Событие не найдено")
        from datetime import datetime
        if event.date <= datetime.utcnow():
            raise HTTPException(status_code=400, detail="Нельзя забронировать событие, которое уже началось")
        if event.seats < booking.seats:
            raise HTTPException(status_code=400, detail="Недостаточно свободных мест")
        raise HTTPException(status_code=400, detail="Невозможно создать бронирование")
    return created

@app.get("/bookings/me", response_model=List[BookingResponse])
def my_bookings(db: Session = Depends(get_db), current_user: User = Depends(verify_signature)):
    bookings = get_user_bookings(db, current_user.id)
    return [b for b in bookings if b.event_id is not None]

@app.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking_detail(booking_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(verify_signature)):
    booking = get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return booking

@app.patch("/bookings/{booking_id}", response_model=BookingResponse)
def update_booking_endpoint(booking_id: int, data: dict, db: Session = Depends(get_db),
                            current_user: User = Depends(verify_signature)):
    allow_admin = current_user.role == "admin"
    updated = update_booking(db, booking_id, data, current_user.id, allow_admin=allow_admin)
    if not updated:
        raise HTTPException(status_code=404, detail="Booking not found or not authorized")
    return updated

@app.delete("/bookings/{booking_id}", response_model=BookingResponse)
def cancel_booking_endpoint(booking_id: int, db: Session = Depends(get_db),
                            current_user: User = Depends(verify_signature)):
    allow_admin = current_user.role == "admin"
    cancelled = cancel_booking(db, booking_id, current_user.id, allow_admin=allow_admin)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Booking not found")
    return cancelled

@app.post("/reviews", response_model=ReviewResponse)
def add_review(review: ReviewCreate, db: Session = Depends(get_db),
               current_user: User = Depends(verify_signature)):
    result = create_review(db, review, user_id=current_user.id)
    if not result:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create review: you must have a booking for this event, the event must be in the past, and you can only leave one review per event"
        )
    return {
        "id": result.id,
        "text": result.text,
        "rating": result.rating,
        "user_id": result.user_id,
        "event_id": result.event_id,
        "is_edited": result.is_edited if hasattr(result, 'is_edited') else 0,
        "username": result.user.username if result.user else None,
        "event_title": result.event.title if result.event else None
    }

@app.get("/reviews/event/{event_id}", response_model=List[ReviewResponse])
def event_reviews(event_id: int, db: Session = Depends(get_db)):
    reviews = get_reviews_by_event(db, event_id)
    result = []
    for review in reviews:
        review_dict = {
            "id": review.id,
            "text": review.text,
            "rating": review.rating,
            "user_id": review.user_id,
            "event_id": review.event_id,
            "is_edited": review.is_edited if hasattr(review, 'is_edited') else 0,
            "username": review.user.username if review.user else None,
            "event_title": review.event.title if review.event else None
        }
        result.append(review_dict)
    return result

@app.patch("/reviews/{review_id}", response_model=ReviewResponse)
def update_review_endpoint(review_id: int, data: dict, db: Session = Depends(get_db),
                           current_user: User = Depends(verify_signature)):
    updated = update_review(db, review_id, data, current_user.id, allow_admin=False)
    if not updated:
        raise HTTPException(status_code=404, detail="Review not found or not authorized")
    return {
        "id": updated.id,
        "text": updated.text,
        "rating": updated.rating,
        "user_id": updated.user_id,
        "event_id": updated.event_id,
        "is_edited": updated.is_edited if hasattr(updated, 'is_edited') else 0,
        "username": updated.user.username if updated.user else None,
        "event_title": updated.event.title if updated.event else None
    }

@app.delete("/reviews/{review_id}", response_model=ReviewResponse)
def delete_review_endpoint(review_id: int, db: Session = Depends(get_db),
                           current_user: User = Depends(verify_signature)):
    allow_admin = current_user.role == "admin"
    deleted = delete_review(db, review_id, current_user.id, allow_admin=allow_admin)
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found or not authorized")
    return deleted

@app.get("/events/search", response_model=List[EventResponse])
def search_events(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return db.query(Event).filter(Event.title.contains(q)).all()
