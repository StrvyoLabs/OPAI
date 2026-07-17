from app.services.appointment_service import AppointmentService
from app.services.crm_service import CRMService
from app.services.email_service import EmailService
from app.services.equipment_service import EquipmentService
from app.services.invoice_service import InvoiceService
from app.services.maintenance_reminder_service import MaintenanceReminderService
from app.services.reminder_service import ReminderService
from app.services.storage_service import SupabaseStorageService
from app.services.whatsapp_service import WhatsAppService
from app.tools.crm_tools import FindOrCreateCustomerTool
from app.tools.hvac_tools import AddEquipmentTool, MarkInvoicePaidTool, ScheduleMaintenanceReminderTool
from app.tools.invoice_tools import GenerateInvoicePdfTool, SendEmailTool
from app.tools.registry import ToolRegistry
from app.tools.sample_tools import CreateNoteTool, SendWhatsAppMessageTool, WebSearchTool
from app.tools.scheduling_tools import CreateAppointmentTool, CreatePaymentReminderTool


def register_default_tools(
    registry: ToolRegistry,
    *,
    whatsapp_service: WhatsAppService,
    storage_service: SupabaseStorageService,
    email_service: EmailService,
    crm_service: CRMService,
    invoice_service: InvoiceService,
    appointment_service: AppointmentService,
    reminder_service: ReminderService,
    equipment_service: EquipmentService,
    maintenance_reminder_service: MaintenanceReminderService,
    currency_symbol: str,
    business_timezone: str,
) -> None:
    registry.register(SendWhatsAppMessageTool(whatsapp_service))
    registry.register(CreateNoteTool())
    registry.register(WebSearchTool())
    registry.register(
        FindOrCreateCustomerTool(
            crm_service,
            appointment_service,
            invoice_service,
            equipment_service,
            maintenance_reminder_service,
            business_timezone,
        )
    )
    registry.register(
        GenerateInvoicePdfTool(storage_service, crm_service, invoice_service, currency_symbol)
    )
    registry.register(SendEmailTool(email_service))
    registry.register(CreateAppointmentTool(crm_service, appointment_service, business_timezone))
    registry.register(CreatePaymentReminderTool(crm_service, invoice_service, reminder_service))
    registry.register(MarkInvoicePaidTool(crm_service, invoice_service))
    registry.register(AddEquipmentTool(crm_service, equipment_service))
    registry.register(ScheduleMaintenanceReminderTool(crm_service, maintenance_reminder_service))
