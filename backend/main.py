from contextlib import asynccontextmanager
from pathlib import Path
import os
import signal
import subprocess
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.api import router
from app.core.config import settings
from app.core.database import Base, close_redis, engine, init_redis

Base.metadata.create_all(bind=engine)


def ensure_runtime_schema() -> None:
    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info('daily_tasks')").fetchall()
        }
        if "status" not in columns:
            connection.exec_driver_sql("ALTER TABLE daily_tasks ADD COLUMN status VARCHAR(20) DEFAULT 'pending' NOT NULL")
        if "completed_at" not in columns:
            connection.exec_driver_sql("ALTER TABLE daily_tasks ADD COLUMN completed_at DATETIME")


ensure_runtime_schema()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting application...")
    await init_redis()
    yield
    print("Shutting down application...")
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description="物联网养殖大棚监测与控制系统后端 API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "status": "running",
        "app_name": settings.APP_NAME,
        "version": settings.API_VERSION,
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "debug": settings.DEBUG,
    }


def start_frontend_dev_server() -> subprocess.Popen | None:
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if not frontend_dir.exists():
        print(f"Frontend directory not found: {frontend_dir}")
        return None

    npm_command = "npm.cmd" if os.name == "nt" else "npm"
    creation_flags = 0
    command = [npm_command, "run", "dev", "--", "--host", "0.0.0.0"]

    if os.name == "nt":
        creation_flags = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        process = subprocess.Popen(
            command,
            cwd=frontend_dir,
            creationflags=creation_flags,
        )
        print("[Frontend] started in a separate console: http://localhost:5173")
        return process
    except FileNotFoundError:
        print("npm not found. Please install Node.js or run with --backend-only.")
        return None


def stop_frontend_dev_server(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return

    try:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.terminate()
        process.wait(timeout=5)
    except Exception:
        process.kill()


if __name__ == "__main__":
    import uvicorn

    frontend_process = None
    backend_only = "--backend-only" in sys.argv

    try:
        if not backend_only:
            print("[Launcher] starting frontend in a separate console window...")
            frontend_process = start_frontend_dev_server()

        print("[Backend] starting FastAPI server in current console: http://localhost:8000")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.DEBUG,
        )
    finally:
        stop_frontend_dev_server(frontend_process)
