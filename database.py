#настройка подключения к базе данных: создание engine SQLAlchemy, сессий и базового класса для моделей

from sqlalchemy import create_engine  #Импорт create_engine для создания подключения к БД
from sqlalchemy.ext.declarative import declarative_base  #Импорт declarative_base для создания базового класса моделей
from sqlalchemy.orm import sessionmaker  #Импорт sessionmaker для создания фабрики сессий

SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"  #URL подключения к SQLite БД (файл database.db в текущей директории)

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})  #Создание engine для подключения к БД с отключением проверки потока для SQLite
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  #Создание фабрики сессий: без автокоммита, без автофлаша, привязка к engine

Base = declarative_base()  #Создание базового класса для всех моделей SQLAlchemy