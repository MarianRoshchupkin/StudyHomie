import os
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    JSON,
    create_engine,
    CheckConstraint,
    DateTime,
    text
)
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    subjects = Column(JSON)  # Список предметов в формате JSON
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )


class Resource(Base):
    __tablename__ = 'resources'

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    link = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        CheckConstraint(
            "type IN ('Article', 'Video', 'Tutorial')",
            name='check_resource_type'
        ),
    )


# Создание SessionLocal для использования в других модулях
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Инициализация базы данных и создание таблиц
def init_db():
    Base.metadata.create_all(engine)
    print("Таблицы успешно созданы!")


if __name__ == '__main__':
    init_db()
