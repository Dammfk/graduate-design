from typing import Optional

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings


if "sqlite" in settings.SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=20,
        max_overflow=0,
    )


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


async def init_redis() -> None:
    global redis_client
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        print("[Redis] connected")
    except Exception as exc:
        print(f"[Redis] connection failed: {exc}. Running without cache.")
        redis_client = None


async def close_redis() -> None:
    global redis_client
    if redis_client:
        redis_client.close()
        redis_client = None
        print("[Redis] connection closed")
