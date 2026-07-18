from functools import lru_cache

from app.core.config import get_settings
from app.db.session import async_session_maker
from app.llm.base import PlannerLLM
from app.llm.groq_planner import GroqPlannerLLM
from app.services.activity_service import ActivityService
from app.services.appointment_service import AppointmentService
from app.services.crm_service import CRMService
from app.services.email_service import EmailService, GmailSMTPEmailService, ResendEmailService
from app.services.equipment_service import EquipmentService
from app.services.executor_service import ExecutorService
from app.services.invoice_service import InvoiceService
from app.services.maintenance_reminder_service import MaintenanceReminderService
from app.services.orchestrator import TaskOrchestrator
from app.services.planner_service import PlannerService
from app.services.reminder_scheduler import ReminderScheduler
from app.services.reminder_service import ReminderService
from app.services.storage_service import SupabaseStorageService
from app.services.whatsapp_service import WhatsAppService
from app.tools.registry import ToolRegistry, tool_registry
from app.tools.setup import register_default_tools


@lru_cache
def get_whatsapp_service() -> WhatsAppService:
    return WhatsAppService(get_settings())


@lru_cache
def get_storage_service() -> SupabaseStorageService:
    return SupabaseStorageService(get_settings())


@lru_cache
def get_email_service() -> EmailService:
    settings = get_settings()
    if settings.email_provider == "gmail":
        return GmailSMTPEmailService(settings)
    return ResendEmailService(settings)


@lru_cache
def get_crm_service() -> CRMService:
    return CRMService(async_session_maker)


@lru_cache
def get_invoice_service() -> InvoiceService:
    return InvoiceService(async_session_maker)


@lru_cache
def get_appointment_service() -> AppointmentService:
    return AppointmentService(async_session_maker)


@lru_cache
def get_reminder_service() -> ReminderService:
    return ReminderService(async_session_maker)


@lru_cache
def get_equipment_service() -> EquipmentService:
    return EquipmentService(async_session_maker)


@lru_cache
def get_maintenance_reminder_service() -> MaintenanceReminderService:
    return MaintenanceReminderService(async_session_maker)


@lru_cache
def get_reminder_scheduler() -> ReminderScheduler:
    return ReminderScheduler(async_session_maker, get_whatsapp_service())


@lru_cache
def get_tool_registry() -> ToolRegistry:
    settings = get_settings()
    register_default_tools(
        tool_registry,
        whatsapp_service=get_whatsapp_service(),
        storage_service=get_storage_service(),
        email_service=get_email_service(),
        crm_service=get_crm_service(),
        invoice_service=get_invoice_service(),
        appointment_service=get_appointment_service(),
        reminder_service=get_reminder_service(),
        equipment_service=get_equipment_service(),
        maintenance_reminder_service=get_maintenance_reminder_service(),
        currency_symbol=settings.invoice_currency_symbol,
        business_timezone=settings.business_timezone,
    )
    return tool_registry


@lru_cache
def get_planner_llm() -> PlannerLLM:
    settings = get_settings()
    return GroqPlannerLLM(
        api_key=settings.groq_api_key,
        model=settings.planner_model,
        base_url=settings.groq_base_url,
    )


def get_activity_service() -> ActivityService:
    return ActivityService()


def get_planner_service() -> PlannerService:
    return PlannerService(
        get_planner_llm(),
        get_tool_registry(),
        get_activity_service(),
        get_crm_service(),
        get_settings().business_timezone,
    )


def get_executor_service() -> ExecutorService:
    return ExecutorService(get_tool_registry(), get_activity_service(), get_planner_llm())


def get_orchestrator() -> TaskOrchestrator:
    return TaskOrchestrator(get_planner_service(), get_executor_service())
