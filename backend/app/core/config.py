from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]

    database_url: str

    # IANA timezone the business operates in -- used to resolve relative
    # dates/times ("Friday at 2 PM") in owner requests to the correct
    # local time, not UTC.
    business_timezone: str = "Asia/Kolkata"

    # Planner LLM -- Groq's OpenAI-compatible API.
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    planner_model: str = "llama-3.3-70b-versatile"

    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_api_version: str = "v21.0"

    # Supabase Storage -- holds generated invoice PDFs.
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "invoices"
    invoice_currency_symbol: str = "₹"

    # Email -- "resend" or "gmail".
    email_provider: str = "resend"

    # Resend -- transactional email. Can't send from a gmail.com address
    # (requires DNS-verified domain ownership); use "gmail" provider for that.
    resend_api_key: str = ""
    resend_from_email: str = "onboarding@resend.dev"

    # Gmail SMTP -- sends from a real Gmail address via an App Password,
    # no custom domain needed. Generate one at myaccount.google.com/apppasswords
    # (requires 2-Step Verification enabled on the account).
    gmail_address: str = ""
    gmail_app_password: str = ""

    @property
    def whatsapp_graph_url(self) -> str:
        return f"https://graph.facebook.com/{self.whatsapp_api_version}/{self.whatsapp_phone_number_id}/messages"

    @property
    def supabase_storage_url(self) -> str:
        return f"{self.supabase_url}/storage/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
