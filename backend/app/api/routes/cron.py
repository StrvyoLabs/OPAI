from fastapi import APIRouter, Header, HTTPException

from app.core.config import get_settings
from app.core.deps import get_reminder_scheduler

router = APIRouter(prefix="/cron", tags=["cron"])


@router.get("/check-reminders")
async def check_reminders(authorization: str | None = Header(default=None)) -> dict:
    settings = get_settings()
    if settings.cron_secret:
        expected = f"Bearer {settings.cron_secret}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    return await get_reminder_scheduler().run_once()
