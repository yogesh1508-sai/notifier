"""
notifications.py — Birthday notification channels
"""

from datetime import date, datetime
from typing import Protocol
from models import Employee
import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ── Notification channel protocol ────────────────────────────────────────────

class NotificationChannel(Protocol):
    def send_birthday_alert(self, employee: Employee) -> bool: ...
    def send_team_greeting(self, employee: Employee, channel: str) -> bool: ...


# ── Console (always available) ────────────────────────────────────────────────

class ConsoleNotifier:
    """Rich console output — no external dependencies."""

    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    MAGENTA= "\033[95m"
    RED    = "\033[91m"

    def send_birthday_alert(self, employee: Employee) -> bool:
        print(f"\n{self.YELLOW}{'='*60}{self.RESET}")
        print(f"{self.BOLD}{self.YELLOW}  🎉  BIRTHDAY ALERT!{self.RESET}")
        print(f"{self.YELLOW}{'='*60}{self.RESET}")
        print(f"  {self.CYAN}Name      :{self.RESET} {self.BOLD}{employee.name}{self.RESET}")
        print(f"  {self.CYAN}Employee  :{self.RESET} {employee.employee_id}")
        print(f"  {self.CYAN}Department:{self.RESET} {employee.department}")
        print(f"  {self.CYAN}Turning   :{self.RESET} {employee.age} years old today 🎂")
        print(f"  {self.CYAN}Status    :{self.RESET} {employee.profile_status}")
        print(f"{self.YELLOW}{'='*60}{self.RESET}\n")
        return True

    def send_team_greeting(self, employee: Employee, channel: str = "general") -> bool:
        msg = self._greeting_text(employee)
        print(f"\n{self.GREEN}[TEAM GREETING → #{channel}]{self.RESET}")
        print(f"  {msg}\n")
        return True

    @staticmethod
    def _greeting_text(employee: Employee) -> str:
        return (
            f"🎉 Please join us in wishing {employee.name} from {employee.department} "
            f"a very Happy Birthday! Wishing you a wonderful {employee.age}th year ahead! 🎂🥳"
        )


# ── Email notifier ────────────────────────────────────────────────────────────

class EmailNotifier:
    """
    Sends birthday emails via SMTP.
    Configure via environment variables:
        SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
        HR_EMAIL (sender), TEAM_EMAIL (mailing list)
    """

    def __init__(self):
        self.host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port     = int(os.getenv("SMTP_PORT", 587))
        self.user     = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASS", "")
        self.sender   = os.getenv("HR_EMAIL", self.user)
        self.team     = os.getenv("TEAM_EMAIL", "team@company.com")
        self._configured = bool(self.user and self.password)

    def send_birthday_alert(self, employee: Employee) -> bool:
        if not self._configured:
            print(f"  [Email] ⚠  Not configured — skipping alert for {employee.name}")
            return False
        subject = f"🎂 Birthday Reminder: {employee.name} celebrates today!"
        body    = self._alert_html(employee)
        return self._send(self.sender, subject, body)

    def send_team_greeting(self, employee: Employee, channel: str = "") -> bool:
        if not self._configured:
            print(f"  [Email] ⚠  Not configured — skipping greeting for {employee.name}")
            return False
        subject = f"🎉 Happy Birthday {employee.name}!"
        body    = self._greeting_html(employee)
        return self._send(self.team, subject, body)

    # ── internal helpers ─────────────────────────────────────────────────────

    def _send(self, to: str, subject: str, html: str) -> bool:
        try:
            msg                  = MIMEMultipart("alternative")
            msg["Subject"]       = subject
            msg["From"]          = self.sender
            msg["To"]            = to
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.sender, to, msg.as_string())
            print(f"  [Email] ✅  Sent to {to}")
            return True
        except Exception as exc:
            print(f"  [Email] ❌  Failed: {exc}")
            return False

    @staticmethod
    def _alert_html(e: Employee) -> str:
        return f"""
        <html><body>
        <h2>🎂 Birthday Reminder</h2>
        <p>Today is <strong>{e.name}</strong>'s birthday!</p>
        <ul>
          <li><b>Employee ID:</b> {e.employee_id}</li>
          <li><b>Department:</b>  {e.department}</li>
          <li><b>Turning:</b>     {e.age} years old</li>
        </ul>
        <p>Please take a moment to wish them a wonderful day! 🎉</p>
        </body></html>"""

    @staticmethod
    def _greeting_html(e: Employee) -> str:
        return f"""
        <html><body>
        <h2>🎉 Happy Birthday, {e.name}!</h2>
        <p>On behalf of the entire team, we wish you a very Happy {e.age}th Birthday!</p>
        <p>Thank you for being an amazing part of our {e.department} team. 
           Wishing you joy, success, and celebration today and always! 🥳🎂</p>
        </body></html>"""


# ── Microsoft Teams notifier (webhook) ───────────────────────────────────────

class TeamsNotifier:
    """
    Posts an Adaptive Card to a Teams channel via Incoming Webhook.
    Set TEAMS_WEBHOOK_URL in environment.
    """

    def __init__(self):
        self.webhook_url = os.getenv("TEAMS_WEBHOOK_URL", "")
        self._configured = bool(self.webhook_url)

    def send_birthday_alert(self, employee: Employee) -> bool:
        return self._post(self._build_card(employee, alert=True))

    def send_team_greeting(self, employee: Employee, channel: str = "") -> bool:
        return self._post(self._build_card(employee, alert=False))

    def _post(self, payload: dict) -> bool:
        if not self._configured:
            print("  [Teams] ⚠  TEAMS_WEBHOOK_URL not set — skipping.")
            return False
        try:
            import urllib.request
            data = json.dumps(payload).encode()
            req  = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                ok = resp.status == 200
                print(f"  [Teams] {'✅' if ok else '❌'}  HTTP {resp.status}")
                return ok
        except Exception as exc:
            print(f"  [Teams] ❌  {exc}")
            return False

    @staticmethod
    def _build_card(e: Employee, alert: bool) -> dict:
        title = (
            f"🎂 Birthday Reminder: {e.name}" if alert
            else f"🎉 Happy Birthday, {e.name}!"
        )
        text = (
            f"**{e.name}** from **{e.department}** is celebrating their **{e.age}th birthday** today! 🥳"
        )
        return {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type":    "AdaptiveCard",
                    "version": "1.3",
                    "body": [
                        {"type": "TextBlock", "size": "Large",  "weight": "Bolder", "text": title},
                        {"type": "TextBlock", "wrap": True,     "text": text},
                        {"type": "FactSet",   "facts": [
                            {"title": "Employee ID",  "value": e.employee_id},
                            {"title": "Department",   "value": e.department},
                            {"title": "Turning",      "value": f"{e.age} today"},
                        ]},
                    ],
                },
            }],
        }


# ── Slack notifier (webhook) ─────────────────────────────────────────────────

class SlackNotifier:
    """
    Posts a birthday message to Slack via Incoming Webhook.
    Set SLACK_WEBHOOK_URL in environment.
    """

    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self._configured = bool(self.webhook_url)

    def send_birthday_alert(self, employee: Employee) -> bool:
        return self._post(self._build_alert(employee))

    def send_team_greeting(self, employee: Employee, channel: str = "general") -> bool:
        return self._post(self._build_greeting(employee))

    def _post(self, payload: dict) -> bool:
        if not self._configured:
            print("  [Slack] ⚠  SLACK_WEBHOOK_URL not set — skipping.")
            return False
        try:
            import urllib.request
            data = json.dumps(payload).encode()
            req  = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                ok = resp.read() == b"ok"
                print(f"  [Slack] {'✅' if ok else '❌'}  Response received")
                return ok
        except Exception as exc:
            print(f"  [Slack] ❌  {exc}")
            return False

    @staticmethod
    def _build_alert(e: Employee) -> dict:
        return {
            "blocks": [
                {"type": "header",  "text": {"type": "plain_text", "text": f"🎂 Birthday Alert: {e.name}"}},
                {"type": "section", "fields": [
                    {"type": "mrkdwn", "text": f"*Employee:*\n{e.employee_id}"},
                    {"type": "mrkdwn", "text": f"*Department:*\n{e.department}"},
                    {"type": "mrkdwn", "text": f"*Turning:*\n{e.age} today 🎉"},
                ]},
            ]
        }

    @staticmethod
    def _build_greeting(e: Employee) -> dict:
        return {
            "text": (
                f"🎉 Please join us in wishing *{e.name}* from *{e.department}* "
                f"a very Happy *{e.age}th Birthday*! 🎂🥳"
            )
        }


# ── Notification manager ─────────────────────────────────────────────────────

class NotificationManager:
    """Broadcasts to all registered channels."""

    def __init__(self, channels: list = None):
        self.channels: list = channels or [ConsoleNotifier()]

    def add_channel(self, channel) -> None:
        self.channels.append(channel)

    def notify_birthday(self, employee: Employee, send_greeting: bool = True) -> dict:
        results = {}
        for ch in self.channels:
            name = type(ch).__name__
            results[name] = {}
            results[name]["alert"]    = ch.send_birthday_alert(employee)
            if send_greeting:
                results[name]["greeting"] = ch.send_team_greeting(employee, "general")
        return results

    def notify_all_birthdays(self, employees: list[Employee]) -> None:
        if not employees:
            print("\n  ℹ  No birthdays today.\n")
            return
        for emp in employees:
            self.notify_birthday(emp)
