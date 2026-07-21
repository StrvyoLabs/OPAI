import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import activity, crm, planner, tasks, whatsapp, ws
from app.core.config import get_settings
from app.core.deps import get_reminder_scheduler

logging.basicConfig(level=logging.INFO)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_task = asyncio.create_task(get_reminder_scheduler().run_forever())
    yield
    scheduler_task.cancel()


app = FastAPI(title="Operator AI", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(whatsapp.router)
app.include_router(planner.router)
app.include_router(tasks.router)
app.include_router(activity.router)
app.include_router(crm.router)
app.include_router(ws.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}
