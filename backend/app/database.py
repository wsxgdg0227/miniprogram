# -*- coding: gbk -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


# connect_args 仅在 SQLite 下使用，用于告诉驱动允许跨线程访问同一个连接。
connect_args = {"check_same_thread": False} if "sqlite" in settings.db_url else {}
engine = create_engine(settings.db_url, connect_args=connect_args)

# SessionLocal 是“数据库会话工厂”。
# 每次请求都会从这个工厂创建一个新的 Session，用完后关闭，避免连接泄漏。
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# DeclarativeBase 是 SQLAlchemy 2.0 推荐的 ORM 基类写法。
# 所有模型类都会继承 Base，从而映射到数据库表。
class Base(DeclarativeBase):
    pass
