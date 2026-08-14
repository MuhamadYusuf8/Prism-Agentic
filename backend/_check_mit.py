"""Check the mit@president.ac.id conversation in the monitoring module."""
import asyncio
import httpx


async def main():
    base = "http://localhost:8000"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            f"{base}/api/email/monitoring/conversations",
            params={"search": "mit@president.ac.id"},
        )
        print("SEARCH STATUS", r.status_code)
        data = r.json()
        print("total:", data.get("total"))
        for conv in data.get("data", []):
            print("  -", conv["lead_name"], "|", conv["recipient_email"], "|", conv["status"],
                  "| emails", conv["emails_sent"], "| last", conv["last_activity_at"])
            thread = await c.get(
                f"{base}/api/email/monitoring/conversations/{conv.get('lead_id') or conv.get('recipient_email')}"
            )
            print("  THREAD:", thread.status_code, "| status", thread.json().get("status"),
                  "| messages", thread.json().get("messages_count"), "| sender",
                  thread.json().get("sender_email"))
            for m in thread.json().get("messages", []):
                print("     ", m["direction"], "|", m["type"], "|", (m.get("subject") or "")[:45],
                      "|", m.get("sent_at"), "| status:", m.get("status"),
                      "| error:", (m.get("error_message") or "")[:60])


asyncio.run(main())
