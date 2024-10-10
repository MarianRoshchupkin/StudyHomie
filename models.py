import os
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    JSON,
    create_engine,
    CheckConstraint,
    TIMESTAMP,
    Table,
)
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from dotenv import load_dotenv
from datetime import datetime

# Загрузка переменных окружения из .env файла
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

Base = declarative_base()

# Промежуточная таблица для связи пользователей и групп
user_groups = Table(
    'user_groups',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('discussion_groups.id'), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    subjects = Column(JSON)  # Список предметов в формате JSON
    progress = Column(JSON)  # Опционально: информация о прогрессе пользователя
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(
        TIMESTAMP,
        server_default="CURRENT_TIMESTAMP",
        onupdate="CURRENT_TIMESTAMP"
    )

    groups = relationship(
        'DiscussionGroup',
        secondary=user_groups,
        back_populates='members'
    )


class Resource(Base):
    __tablename__ = 'resources'

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    link = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

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
