#определение зависимостей, используемых в FastAPI - функция для получения сессии БД, которая инжектируется в эндпоинты

from sqlalchemy.orm import Session  #Импорт Session для работы с сессиями БД
from database import SessionLocal  #Импорт SessionLocal из database.py для создания сессий

def get_db():  #Функция-генератор для получения сессии БД
    db = SessionLocal()  #Создание новой сессии БД
    try:  #Блок try для обеспечения закрытия сессии
        yield db  #Yield сессии для использования в зависимостях FastAPI
    finally:  #Блок finally для закрытия сессии после использования
        db.close()  #Закрытие сессии БД