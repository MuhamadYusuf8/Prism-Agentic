"""
IMAP Mailbox Monitor — ingests incoming replies from our mailbox.

Connects to the admissions mailbox (e.g. mit@president.ac.id) over IMAP,
decodes unread messages, and hands them to the reply pipeline so they are
stored as `Reply` records, linked to the matching student lead, and shown in
the conversation/monitoring module.

Configuration (from backend/.env):
    IMAP_HOST       e.g. imap.google.com (Google Workspace) or mail.president.ac.id
    IMAP_PORT       993 (SSL) or 143 (STARTTLS)
    IMAP_USERNAME   the mailbox address, e.g. mit@president.ac.id
    IMAP_PASSWORD   app password / mailbox password
    IMAP_USE_SSL    true for 993, false for 143
"""

from __future__ import annotations

import email
import imaplib
from datetime import datetime, timezone
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.reply import Reply


# ── Decoding helpers ──────────────────────────────────────────────────────────


def _decode_header_value(value: Any) -> str:
    """Decode RFC2047-encoded header value to a plain string."""
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="replace")
            except Exception:
                return ""
        return str(value)


def _get_message_body(msg: Message) -> tuple[str | None, str | None]:
    """Extract (text, html) parts from an email Message."""
    text = None
    html = None

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition") or "")
            if "attachment" in cdisp:
                continue
            try:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
            except Exception:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except LookupError:
                decoded = payload.decode("utf-8", errors="replace")
            if ctype == "text/plain" and text is None:
                text = decoded
            elif ctype == "text/html" and html is None:
                html = decoded
    else:
        try:
            payload = msg.get_payload(decode=True)
        except Exception:
            payload = None
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except LookupError:
                decoded = payload.decode("utf-8", errors="replace")
            if msg.get_content_type() == "text/html":
                html = decoded
            else:
                text = decoded

    return text, html


def parse_message(raw: bytes) -> dict:
    """Parse a raw RFC822 message into a plain dict for the pipeline."""
    msg = email.message_from_bytes(raw)
    subject = _decode_header_value(msg.get("Subject"))
    from_header = _decode_header_value(msg.get("From"))
    message_id = _decode_header_value(msg.get("Message-ID"))
    date_header = msg.get("Date")

    received_at = None
    if date_header:
        try:
            received_at = parsedate_to_datetime(date_header)
            if received_at.tzinfo is None:
                received_at = received_at.replace(tzinfo=timezone.utc)
        except Exception:
            received_at = None

    # Parse the From: "Name <email>" into an address
    from_email = from_header
    if "<" in from_header and ">" in from_header:
        start = from_header.rfind("<") + 1
        end = from_header.rfind(">")
        from_email = from_header[start:end].strip()
    from_email = from_email.strip().lower()

    text, html = _get_message_body(msg)

    return {
        "from_email": from_email,
        "from_name": from_header,
        "subject": subject or "",
        "message_id": message_id,
        "received_at": received_at,
        "body_text": text,
        "body_html": html,
        "raw": raw,
    }


# ── IMAP fetching (blocking — run via asyncio.to_thread) ─────────────────────


def fetch_unseen_messages(
    host: str,
    username: str,
    password: str,
    port: int = 993,
    use_ssl: bool = True,
    folder: str = "INBOX",
    limit: int = 50,
) -> list[dict]:
    """Fetch unread messages from the mailbox over IMAP (blocking)."""
    if not host or not username or not password:
        return []

    if use_ssl:
        mail = imaplib.IMAP4_SSL(host, port)
    else:
        mail = imaplib.IMAP4(host, port)
        mail.starttls()

    messages: list[dict] = []
    try:
        mail.login(username, password)
        mail.select(folder)

        # Search for unseen messages
        typ, data = mail.search(None, "UNSEEN")
        if typ != "OK":
            return messages

        ids = (data[0] or b"").split()
        # Only process the most recent `limit` messages to keep requests bounded
        ids = ids[-limit:]

        for num in ids:
            typ, msg_data = mail.fetch(num, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            try:
                messages.append(parse_message(raw))
            except Exception:
                continue
    finally:
        try:
            mail.logout()
        except Exception:
            pass

    return messages


# ── Async ingestion ───────────────────────────────────────────────────────────


async def already_processed(db: AsyncSession, message_id: str) -> bool:
    """True if a reply with this Message-ID was already ingested."""
    if not message_id:
        return False
    result = await db.execute(
        select(Reply.id).where(
            Reply.raw_data["message_id"].astext == message_id
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def sync_inbox(db: AsyncSession, limit: int = 50) -> dict:
    """
    Fetch unread replies from the configured mailbox and ingest them.

    Returns a summary of how many messages were found, matched to a lead,
    and stored as replies.
    """
    if not (settings.IMAP_HOST and settings.IMAP_USERNAME and settings.IMAP_PASSWORD):
        return {
            "success": False,
            "configured": False,
            "message": (
                "IMAP not configured. Set IMAP_HOST / IMAP_USERNAME / IMAP_PASSWORD "
                "in backend/.env to monitor the mailbox."
            ),
            "fetched": 0,
            "matched": 0,
            "processed": 0,
            "skipped_duplicate": 0,
        }

    import asyncio

    messages = await asyncio.to_thread(
        fetch_unseen_messages,
        settings.IMAP_HOST,
        settings.IMAP_USERNAME,
        settings.IMAP_PASSWORD,
        settings.IMAP_PORT,
        settings.IMAP_USE_SSL,
        limit=limit,
    )

    if not messages:
        return {
            "success": True,
            "configured": True,
            "fetched": 0,
            "matched": 0,
            "processed": 0,
            "skipped_duplicate": 0,
            "message": "No unread messages found in the mailbox.",
        }

    from app.services.reply_monitor import process_reply

    processed = 0
    matched = 0
    skipped_duplicate = 0
    errors = []

    for msg in messages:
        if await already_processed(db, msg["message_id"]):
            skipped_duplicate += 1
            continue

        # Choose the best body: prefer plain text, fall back to stripped HTML
        body_text = msg["body_text"]
        body = msg["body_html"] or body_text or ""

        try:
            result = await process_reply(
                from_email=msg["from_email"],
                subject=msg["subject"] or None,
                body=body,
                body_text=body_text,
                db=db,
            )
            processed += 1
            if result.get("success"):
                matched += 1
                # Tag the reply with the original Message-ID for dedup
                reply = await db.get(Reply, result["reply_id"])
                if reply:
                    reply.raw_data = reply.raw_data or {}
                    reply.raw_data["message_id"] = msg["message_id"]
                    reply.raw_data["received_at_raw"] = (
                        msg["received_at"].isoformat() if msg["received_at"] else None
                    )
                    await db.commit()
            else:
                # No matching lead — still record the raw message so it is not lost
                errors.append({"from_email": msg["from_email"], "error": result.get("error")})
        except Exception as exc:  # noqa: BLE001
            errors.append({"from_email": msg["from_email"], "error": str(exc)})

    return {
        "success": True,
        "configured": True,
        "fetched": len(messages),
        "matched": matched,
        "processed": processed,
        "skipped_duplicate": skipped_duplicate,
        "errors": errors[:20],
    }
