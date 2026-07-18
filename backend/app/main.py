import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import activity, cron, crm, planner, tasks, whatsapp
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(title="Operator AI", version="0.1.0")

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
app.include_router(cron.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}


# TEMPORARY: surfaces real tracebacks in the response body to diagnose the
# intermittent 500s on Vercel, since dashboard log access isn't available
# here. Remove before considering the deployment done.
@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        },
    )
