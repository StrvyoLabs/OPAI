import io
import logging
import re
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

from app.services.crm_service import CRMService
from app.services.email_service import EmailConfigError, EmailService
from app.services.invoice_service import InvoiceService
from app.services.storage_service import StorageConfigError, SupabaseStorageService
from app.tools.base import ToolAdapter, ToolResult

logger = logging.getLogger(__name__)


def _render_invoice_pdf(
    invoice_number: str, customer_name: str, items: list[dict], notes: str, currency_symbol: str
) -> tuple[bytes, float]:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"Invoice {invoice_number}")
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Invoice {invoice_number}", styles["Title"]),
        Paragraph(f"Bill to: {customer_name}", styles["Normal"]),
        Spacer(1, 0.3 * inch),
    ]

    table_data = [["Description", "Qty", "Unit price", "Amount"]]
    total = 0.0
    for item in items:
        quantity = float(item["quantity"])
        unit_price = float(item["unit_price"])
        amount = quantity * unit_price
        total += amount
        table_data.append(
            [
                item["description"],
                str(quantity),
                f"{currency_symbol}{unit_price:,.2f}",
                f"{currency_symbol}{amount:,.2f}",
            ]
        )
    table_data.append(["", "", "Total", f"{currency_symbol}{total:,.2f}"])

    table = Table(table_data, colWidths=[3.2 * inch, 0.8 * inch, 1.2 * inch, 1.2 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#1e293b")),
                ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#1e293b")),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ]
        )
    )
    story.append(table)

    if notes:
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph(notes, styles["Normal"]))

    doc.build(story)
    return buffer.getvalue(), total


class GenerateInvoicePdfTool(ToolAdapter):
    name = "generate_invoice_pdf"
    description = (
        "Generate a PDF invoice for a customer, store it, and record it in the CRM "
        "(creating the customer if they're not already on file). Returns a downloadable URL."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string", "description": "Optional; auto-generated if omitted."},
            "customer_name": {"type": "string"},
            "customer_email": {"type": "string"},
            "customer_phone": {"type": "string"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit_price": {"type": "number"},
                    },
                    "required": ["description", "quantity", "unit_price"],
                },
            },
            "notes": {"type": "string"},
        },
        "required": ["customer_name", "items"],
    }

    def __init__(
        self,
        storage_service: SupabaseStorageService,
        crm_service: CRMService,
        invoice_service: InvoiceService,
        currency_symbol: str,
    ) -> None:
        self._storage_service = storage_service
        self._crm_service = crm_service
        self._invoice_service = invoice_service
        self._currency_symbol = currency_symbol

    async def execute(self, tool_input: dict) -> ToolResult:
        customer_name = tool_input.get("customer_name")
        items = tool_input.get("items") or []
        if not customer_name or not items:
            return ToolResult(success=False, error="'customer_name' and 'items' are required")

        invoice_number = tool_input.get("invoice_number") or f"INV-{uuid.uuid4().hex[:8].upper()}"
        notes = tool_input.get("notes", "")

        try:
            customer = await self._crm_service.find_or_create(
                name=customer_name,
                phone=tool_input.get("customer_phone"),
                email=tool_input.get("customer_email"),
            )
            pdf_bytes, total = _render_invoice_pdf(
                invoice_number, customer_name, items, notes, self._currency_symbol
            )
            file_url = await self._storage_service.upload(
                path=f"{invoice_number}.pdf", content=pdf_bytes, content_type="application/pdf"
            )
            description = ", ".join(item["description"] for item in items)
            await self._invoice_service.create(
                invoice_number=invoice_number,
                customer_id=customer.id,
                description=description,
                amount=total,
                currency_symbol=self._currency_symbol,
                file_url=file_url,
            )
        except StorageConfigError as exc:
            return ToolResult(success=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001 - surfaced to caller as a failed step
            logger.exception("generate_invoice_pdf failed")
            return ToolResult(success=False, error=str(exc))

        return ToolResult(
            success=True,
            output={
                "invoice_number": invoice_number,
                "total": total,
                "currency_symbol": self._currency_symbol,
                "file_url": file_url,
                "customer_id": str(customer.id),
                "customer_email": customer.email,
            },
        )


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PLACEHOLDER_LOCAL_PARTS = {"unknown", "placeholder", "example", "test", "none", "n/a", "na", "noemail"}


def _looks_like_placeholder_email(address: str) -> bool:
    if not _EMAIL_RE.match(address):
        return True
    local_part = address.split("@", 1)[0].lower()
    return local_part in _PLACEHOLDER_LOCAL_PARTS


class SendEmailTool(ToolAdapter):
    name = "send_email"
    description = "Send an email to a customer or contact, e.g. to deliver an invoice link."
    input_schema = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient email address."},
            "subject": {"type": "string"},
            "body": {"type": "string", "description": "Plain text or simple HTML body."},
        },
        "required": ["to", "subject", "body"],
    }

    def __init__(self, email_service: EmailService) -> None:
        self._email_service = email_service

    async def execute(self, tool_input: dict) -> ToolResult:
        to = tool_input.get("to")
        subject = tool_input.get("subject")
        body = tool_input.get("body")
        if not to or not subject or not body:
            return ToolResult(success=False, error="'to', 'subject' and 'body' are required")

        if _looks_like_placeholder_email(to):
            return ToolResult(
                success=False,
                error=(
                    f"'{to}' doesn't look like a real email address -- refusing to send rather than "
                    "let it silently bounce. Ask the owner for the correct address."
                ),
            )

        sender_address = self._email_service.sender_address
        if sender_address and to.strip().lower() == sender_address.strip().lower():
            return ToolResult(
                success=False,
                error=(
                    f"'{to}' is this business's own sending address, not a customer's -- refusing to "
                    "send a customer email to it. The customer's real email is probably missing; ask "
                    "the owner for it instead of reusing the business's own address."
                ),
            )

        try:
            response = await self._email_service.send(to=to, subject=subject, html=body)
        except EmailConfigError as exc:
            return ToolResult(success=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("send_email failed")
            return ToolResult(success=False, error=str(exc))

        return ToolResult(success=True, output=response)
