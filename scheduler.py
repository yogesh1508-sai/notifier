"""
scheduler.py — Standalone daily-check script for cron / Task Scheduler

Usage (cron):
    0 9 * * * /usr/bin/python3 /path/to/birthday_system/scheduler.py

Usage (Windows Task Scheduler):
    python scheduler.py

Logs are appended to birthday_check.log.
"""

import os
import sys
import logging
from datetime import datetime

# ── logging ───────────────────────────────────────────────────────────────────
LOG_FILE = os.path.join(os.path.dirname(__file__), "birthday_check.log")
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── resolve project path ──────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from models        import EmployeeDatabase
from notifications import (
    ConsoleNotifier, EmailNotifier,
    TeamsNotifier,   SlackNotifier,
    NotificationManager,
)
from reports import monthly_birthday_report, upcoming_report


def run() -> None:
    log.info("=" * 60)
    log.info("Birthday Notification System — scheduled daily check")
    log.info("=" * 60)

    db = EmployeeDatabase()
    notifier = NotificationManager(channels=[
        ConsoleNotifier(),
        EmailNotifier(),
        TeamsNotifier(),
        SlackNotifier(),
    ])

    # ── today's birthdays ─────────────────────────────────────────────────────
    todays = db.birthdays_today()
    log.info("Employees checked : %d", len(db.all()))
    log.info("Birthdays today   : %d", len(todays))

    if todays:
        for emp in todays:
            log.info("  🎂  %s (%s) — turning %d", emp.name, emp.department, emp.age)
        notifier.notify_all_birthdays(todays)
    else:
        log.info("No birthdays today.")

    # ── upcoming in next 7 days (log only) ────────────────────────────────────
    upcoming = db.upcoming_birthdays(days=7)
    if upcoming:
        log.info("Upcoming (7 days):")
        for e in upcoming:
            log.info("  🔔  %s — in %d day(s)", e.name, e.days_until_birthday)

    # ── monthly report (1st of month only) ───────────────────────────────────
    from datetime import date
    if date.today().day == 1:
        log.info(monthly_birthday_report(db))

    log.info("Daily check complete.\n")


if __name__ == "__main__":
    run()
