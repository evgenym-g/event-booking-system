#Аутентификация: верификация паролей, создание и декодирование JWT-токенов, 
#аутентификация пользователей и получение текущего пользователя на основе токена

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from crud import get_user_by_username, get_user
from dependencies import get_db

SECRET_KEY = "event_booking_system_oH2810f@4130HFpqj23"  #Секретный ключ для подписи JWT
ALGORITHM = "HS256"  #Алгоритм подписи JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30 #Время жизни токена в минутах

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  #Инициализация контекста для хэширования паролей с использованием bcrypt
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")  #Инициализация схемы OAuth2 для извлечения токена из запроса

# Blacklist для revoked токенов (in-memory; в production - Redis)
revoked_tokens = set()

def verify_password(plain: str, hashed: str):  #Функция для верификации пароля
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):  #Функция для создания JWT-токена
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(db: Session, username: str, password: str):  #Функция для аутентификации пользователя
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.password):
        return False  
    return user

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):  #Асинхронная функция для получения текущего пользователя по токену
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if token in revoked_tokens:
            raise credentials_exception
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        # Преобразуем строку в int (токен содержит user.id как строку)
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, user_id)
    if user is None:
        raise credentials_exception
    return user