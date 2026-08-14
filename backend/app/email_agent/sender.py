import resend
from app.core.config import settings

resend.api_key = settings.RESEND_API_KEY


async def send_email(to: str, subject: str, body: str) -> dict:
    params: resend.Emails.SendParams = {
        "from": settings.EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": body.replace("\n", "<br>"),
    }
    email = resend.Emails.send(params)
    return {"resend_id": email["id"], "status": "sent"}
