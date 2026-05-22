"""
reports.py — Monthly and annual birthday report generator
"""

from datetime import date
from collections import defaultdict
from models import Employee, EmployeeDatabase


MONTHS = [
    "January", "February", "March",    "April",   "May",      "June",
    "July",    "August",   "September", "October", "November", "December",
]


def _bar(count: int, total: int, width: int = 20) -> str:
    filled = round(width * count / total) if total else 0
    return "█" * filled + "░" * (width - filled)


def monthly_birthday_report(db: EmployeeDatabase, month: int = None) -> str:
    """Detailed report for a specific month (default = current month)."""
    month = month or date.today().month
    employees = sorted(
        [e for e in db.all() if e.date_of_birth.month == month],
        key=lambda e: e.date_of_birth.day,
    )
    lines = [
        "",
        f"  📅  BIRTHDAY REPORT — {MONTHS[month - 1].upper()} {date.today().year}",
        f"  {'─' * 52}",
    ]
    if not employees:
        lines.append("  No birthdays this month.")
    else:
        lines.append(f"  {'Name':<22} {'ID':<8} {'Department':<14} {'Date':<12} {'Age'}")
        lines.append(f"  {'─'*22} {'─'*8} {'─'*14} {'─'*12} {'─'*3}")
        for e in employees:
            flag = " 🎉" if e.is_birthday_today else ""
            lines.append(
                f"  {e.name:<22} {e.employee_id:<8} {e.department:<14} "
                f"{e.date_of_birth.strftime('%d %b'):<12} {e.age}{flag}"
            )
    lines.append(f"  {'─' * 52}")
    lines.append(f"  Total: {len(employees)} birthday(s) in {MONTHS[month - 1]}")
    lines.append("")
    return "\n".join(lines)


def annual_birthday_report(db: EmployeeDatabase) -> str:
    """Overview of birthdays across all 12 months."""
    all_emp = db.all()
    by_month: dict[int, list[Employee]] = defaultdict(list)
    for e in all_emp:
        by_month[e.date_of_birth.month].append(e)

    total = len(all_emp)
    cur_m = date.today().month

    lines = [
        "",
        "  📊  ANNUAL BIRTHDAY DISTRIBUTION",
        f"  Total employees: {total}",
        f"  {'─' * 56}",
        f"  {'Month':<12} {'Count':>5}   {'Distribution':<22} {'Names'}",
        f"  {'─'*12} {'─'*5}   {'─'*22} {'─'*20}",
    ]
    for m in range(1, 13):
        emps  = by_month[m]
        count = len(emps)
        bar   = _bar(count, total)
        names = ", ".join(e.name.split()[0] for e in emps) if emps else "—"
        flag  = " ◀ current" if m == cur_m else ""
        lines.append(
            f"  {MONTHS[m-1]:<12} {count:>5}   {bar:<22} {names}{flag}"
        )
    lines.append(f"  {'─' * 56}")
    lines.append("")
    return "\n".join(lines)


def upcoming_report(db: EmployeeDatabase, days: int = 30) -> str:
    """Employees with birthdays in the next N days."""
    employees = db.upcoming_birthdays(days)
    lines = [
        "",
        f"  🔔  UPCOMING BIRTHDAYS (next {days} days)",
        f"  {'─' * 52}",
    ]
    if not employees:
        lines.append(f"  No birthdays in the next {days} days.")
    else:
        lines.append(f"  {'Name':<22} {'Department':<16} {'Date':<12} {'In'}")
        lines.append(f"  {'─'*22} {'─'*16} {'─'*12} {'─'*10}")
        for e in employees:
            d = e.days_until_birthday
            lines.append(
                f"  {e.name:<22} {e.department:<16} "
                f"{e.date_of_birth.strftime('%d %b'):<12} {d} day{'s' if d != 1 else ''}"
            )
    lines.append(f"  {'─' * 52}")
    lines.append("")
    return "\n".join(lines)
