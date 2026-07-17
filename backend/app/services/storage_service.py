import logging

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class StorageConfigError(Exception):
    pass


class SupabaseStorageService:
    """Thin client around the Supabase Storage REST API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def _configured(self) -> bool:
        return bool(self._settings.supabase_url and self._settings.supabase_service_role_key)

    async def upload(self, path: str, content: bytes, content_type: str) -> str:
        """Uploads `content` to the configured bucket at `path` and returns a public URL."""

        if not self._configured:
            raise StorageConfigError("Supabase Storage is not configured (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)")

        bucket = self._settings.supabase_storage_bucket
        url = f"{self._settings.supabase_storage_url}/object/{bucket}/{path}"
        headers = {
            "Authorization": f"Bearer {self._settings.supabase_service_role_key}",
            "apikey": self._settings.supabase_service_role_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, content=content)
            response.raise_for_status()

        return f"{self._settings.supabase_storage_url}/object/public/{bucket}/{path}"
