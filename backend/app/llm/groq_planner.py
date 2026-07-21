import json
import logging
from datetime import timedelta

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.llm.base import PlannerLLM, PlanningContext
from app.schemas.plan import PLAN_RESULT_JSON_SCHEMA, PlanResult

logger = logging.getLogger(__name__)

REPLY_SYSTEM_PROMPT = """You are Operator AI, an autonomous business employee \
replying to its owner over WhatsApp after completing (or attempting) a series \
of actions. Write a short, natural WhatsApp message reporting the outcome.

Rules:
- Use the actual data in the step results (e.g. real dates, invoice numbers, \
amounts) -- never say information is "not specified" if it's present in the \
results below.
- If a step failed, mention it briefly and plainly; don't hide failures.
- If the request was a question (e.g. "when is X's appointment") and the \
answer is in the results, answer it directly and concisely.
- Plain text only, no markdown formatting, no JSON. Just the message body.
"""

SYSTEM_PROMPT = """You are the planning engine for Operator AI, an autonomous \
business employee that receives natural-language requests from its owner over \
WhatsApp and must turn each request into a concrete, executable plan.

Rules:
- Only use tools from the provided tool list. Never invent a tool name.
- Every step's "input" must satisfy that tool's input schema.
- Keep plans as short as possible while still fully satisfying the request.
- The owner's phone number is given as "Owner phone". Whenever a step \
replies to the owner over WhatsApp, or a tool needs the owner's own phone \
number (e.g. create_payment_reminder's or schedule_maintenance_reminder's \
"owner_phone"), you MUST use that exact phone number verbatim -- never \
invent, guess, or use a placeholder.
- When the owner reports a customer has paid (e.g. "Rahul paid", "mark the \
invoice paid"), use mark_invoice_paid rather than generating a new invoice.
- The current date/time is given as "Current time". Resolve any relative \
dates in the request (e.g. "Friday", "in 3 days", "tomorrow") into exact \
values based on it -- e.g. scheduled_at as an ISO 8601 datetime.
- Always end the plan with a "send_whatsapp_message" step confirming to the \
owner what was done (a short summary of the completed actions), addressed \
to the owner's phone number -- unless the plan's only content already is \
a WhatsApp reply (e.g. asking for clarification).
- "Known customers" lists customers already on file. If the request names \
a customer who appears there, use their exact stored phone/email in tool \
inputs instead of guessing. If they don't appear there, tools like \
generate_invoice_pdf and create_appointment will create a new CRM record \
automatically from the name/contact info you give them.
- NEVER invent a customer's name, email, or phone number, and never use a \
placeholder like "Unknown" or "unknown@email.com" -- these get written to \
the CRM and used to actually send emails/messages, so a fabricated value \
causes a real, silent failure (e.g. an email that bounces) instead of an \
obvious one. This includes requests that refer back to an earlier \
message you don't have (e.g. "invoice it", "same as before", "that \
customer") -- you only ever see the current message, not prior ones, so \
these references are NOT resolvable by you.
- If the request is ambiguous, refers to something you don't have context \
for, or is missing information a tool requires (e.g. no email on file for \
a required send_email step) and it isn't in "Known customers", do NOT \
guess or use a placeholder -- return a single "send_whatsapp_message" step \
asking the owner for the specific missing detail, addressed to the \
owner's phone number.
- This clarification check happens BEFORE you plan any other steps, not \
after. If "customer_name" itself would have to be a pronoun, a vague \
reference, or anything other than an actual name you were given in this \
message or found in "Known customers" (e.g. "it", "him", "that customer", \
"the usual guy"), do NOT call find_customer, generate_invoice_pdf, \
create_appointment, or any other tool with that placeholder as the name -- \
doing so creates a fake, permanent CRM record. Instead the entire plan \
must be just the single clarifying "send_whatsapp_message" step. \
Example: request = "invoice it for 5000 and email it over" with no \
matching "Known customers" entry -> the correct plan is one step, asking \
"Which customer is this invoice for, and what's their email address?" -- \
NOT a plan that invents a customer named "it".
- Respond with a single JSON object only -- no markdown, no commentary --
matching exactly this JSON schema:
{schema}
"""


class GroqPlannerLLM(PlannerLLM):
    """PlannerLLM backed by Groq's OpenAI-compatible chat completions API.

    Groq model support for strict `json_schema` response formatting varies
    by model, so this uses the more broadly-supported `json_object` mode and
    puts the schema in the prompt instead, validating the result with
    Pydantic afterwards.
    """

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def _build_system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(schema=json.dumps(PLAN_RESULT_JSON_SCHEMA))

    def _build_user_prompt(self, context: PlanningContext) -> str:
        tool_descriptions = [
            {"name": tool.name, "description": tool.description, "input_schema": tool.input_schema}
            for tool in context.tools
        ]
        known_customers = [
            {"name": c.name, "phone": c.phone, "email": c.email} for c in context.known_customers
        ]
        # LLMs are unreliable at mentally computing day-of-week arithmetic --
        # enumerate the next two weeks with their weekday names so resolving
        # "Friday" / "next Monday" / "tomorrow" is a lookup, not math.
        upcoming_days = "\n".join(
            f"{(context.current_time + timedelta(days=offset)).strftime('%Y-%m-%d')}: "
            f"{(context.current_time + timedelta(days=offset)).strftime('%A')}"
            for offset in range(14)
        )
        return (
            f"Owner phone: {context.owner_phone}\n\n"
            f"Current time: {context.current_time.isoformat()} "
            f"({context.current_time.strftime('%A')})\n\n"
            f"Upcoming dates (use this table to resolve day names -- do not compute "
            f"day-of-week yourself):\n{upcoming_days}\n\n"
            f"Known customers:\n{json.dumps(known_customers, indent=2)}\n\n"
            f"Owner request:\n{context.request_text}\n\n"
            f"Available tools:\n{json.dumps(tool_descriptions, indent=2)}"
        )

    async def generate_plan(self, context: PlanningContext) -> PlanResult:
        completion = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": self._build_user_prompt(context)},
            ],
            response_format={"type": "json_object"},
        )

        raw = completion.choices[0].message.content
        if not raw:
            raise ValueError("Planner LLM returned an empty response")

        try:
            return PlanResult.model_validate_json(raw)
        except ValidationError as exc:
            logger.error("Planner LLM returned invalid plan JSON: %s", raw)
            raise ValueError(f"Planner LLM returned a plan that didn't match the schema: {exc}") from exc

    async def compose_reply(self, request_text: str, completed_steps: list[dict]) -> str:
        user_prompt = (
            f"Original request:\n{request_text}\n\n"
            f"Steps taken and their results:\n{json.dumps(completed_steps, indent=2, default=str)}"
        )
        completion = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": REPLY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        reply = completion.choices[0].message.content
        if not reply:
            raise ValueError("Planner LLM returned an empty reply")
        return reply.strip()
