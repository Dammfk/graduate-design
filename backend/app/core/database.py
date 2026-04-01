from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import redis
from typing import AsyncGenerator, Optional
from .config import settings

# SQLAlchemy
if "sqlite" in settings.SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=20,
        max_overflow=0
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Redis
redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """获取 Redis 客户端"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


async def init_redis():
    """初始化 Redis 连接"""
    global redis_client
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        print("✓ Redis connected")
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}. Running without cache.")
        redis_client = None


async def close_redis():
    """关闭 Redis 连接"""
    global redis_client
    if redis_client:
        redis_client.close()
        redis_client = None
        print("✓ Redis connection closed")
