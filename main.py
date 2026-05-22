"""
main.py — Employee Birthday Notification System
Entry point: interactive CLI + daily check scheduler
"""

import os
import sys
import time
import threading
from datetime import date, datetime

from models      import Employee, EmployeeDatabase, DEPARTMENTS, STATUS_OPTIONS
from notifications import (
    ConsoleNotifier, EmailNotifier,
    TeamsNotifier, SlackNotifier,
    NotificationManager,
)
from reports import monthly_birthday_report, annual_birthday_report, upcoming_report


# ── ANSI colours ──────────────────────────────────────────────────────────────

R = "\033[0m"
B = "\033[1m"
Y = "\033[93m"
C = "\033[96m"
G = "\033[92m"
M = "\033[95m"
RE= "\033[91m"
GR= "\033[90m"


def clr():
    os.system("cls" if os.name == "nt" else "clear")


def header():
    print(f"""
{Y}{B}╔══════════════════════════════════════════════════════╗
║       🎂  Employee Birthday Notification System       ║
║              Corporate Communication Platform         ║
╚══════════════════════════════════════════════════════╝{R}
  {GR}Date: {date.today().strftime('%A, %d %B %Y')}{R}
""")


def pause():
    input(f"\n  {GR}Press Enter to continue…{R}")


# ── Input helpers ─────────────────────────────────────────────────────────────

def prompt(label: str, default: str = "") -> str:
    val = input(f"  {C}{label}{R}{f' [{default}]' if default else ''}: ").strip()
    return val or default


def prompt_date(label: str) -> date:
    while True:
        raw = input(f"  {C}{label}{R} (YYYY-MM-DD): ").strip()
        try:
            return date.fromisoformat(raw)
        except ValueError:
            print(f"  {RE}Invalid date. Use YYYY-MM-DD format.{R}")


def choose(label: str, options: list[str]) -> str:
    print(f"\n  {C}{label}{R}")
    for i, o in enumerate(options, 1):
        print(f"    {G}{i}.{R} {o}")
    while True:
        raw = input("  Choice: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"  {RE}Please enter a number between 1 and {len(options)}.{R}")


# ── Daily check (runs on startup + every 24 h) ────────────────────────────────

def daily_check(db: EmployeeDatabase, notifier: NotificationManager,
                verbose: bool = True) -> None:
    birthdays = db.birthdays_today()
    if verbose:
        if birthdays:
            print(f"\n{G}  ✅  Daily check complete — {len(birthdays)} birthday(s) found today!{R}")
        else:
            print(f"\n{GR}  ✅  Daily check complete — no birthdays today.{R}")
    notifier.notify_all_birthdays(birthdays)


def schedule_daily_check(db: EmployeeDatabase, notifier: NotificationManager) -> None:
    """Background thread: run a silent check every 24 hours."""
    def loop():
        while True:
            time.sleep(86400)
            daily_check(db, notifier, verbose=False)
    t = threading.Thread(target=loop, daemon=True)
    t.start()


# ── Menu actions ──────────────────────────────────────────────────────────────

def view_all_employees(db: EmployeeDatabase) -> None:
    clr(); header()
    emps = db.all()
    print(f"  {B}ALL EMPLOYEES  ({len(emps)} records){R}\n")
    print(f"  {'ID':<8} {'Name':<22} {'Department':<14} {'DOB':<12} {'Age':>3}  Status")
    print(f"  {'─'*8} {'─'*22} {'─'*14} {'─'*12} {'─'*3}  {'─'*8}")
    for e in sorted(emps, key=lambda x: x.employee_id):
        flag = f"  {Y}🎉 Birthday!{R}" if e.is_birthday_today else ""
        print(
            f"  {e.employee_id:<8} {e.name:<22} {e.department:<14} "
            f"{e.date_of_birth.strftime('%d %b %Y'):<12} {e.age:>3}  {e.profile_status}{flag}"
        )
    pause()


def add_employee(db: EmployeeDatabase) -> None:
    clr(); header()
    print(f"  {B}ADD NEW EMPLOYEE{R}\n")
    name   = prompt("Full Name")
    emp_id = prompt("Employee ID (e.g. E011)")
    dob    = prompt_date("Date of Birth")
    dept   = choose("Department", DEPARTMENTS)
    status = choose("Profile Status", STATUS_OPTIONS)

    emp = Employee(
        employee_id=emp_id, name=name, date_of_birth=dob,
        department=dept, profile_status=status,
    )
    try:
        db.add(emp)
        print(f"\n  {G}✅  {name} added successfully!{R}")
        if emp.is_birthday_today:
            print(f"  {Y}🎉  And it's their birthday TODAY!{R}")
    except ValueError as err:
        print(f"\n  {RE}❌  {err}{R}")
    pause()


def update_employee(db: EmployeeDatabase) -> None:
    clr(); header()
    print(f"  {B}UPDATE EMPLOYEE{R}\n")
    emp_id = prompt("Employee ID to update")
    emp = db.get(emp_id)
    if not emp:
        print(f"  {RE}Employee '{emp_id}' not found.{R}")
        pause(); return

    print(f"\n  Current: {emp.name} | {emp.department} | {emp.date_of_birth} | {emp.profile_status}")
    print(f"  {GR}(Leave blank to keep current value){R}\n")

    new_name   = prompt("New Name",   emp.name)
    new_dept   = choose("New Department", DEPARTMENTS)
    new_status = choose("New Status", STATUS_OPTIONS)

    db.update(emp_id, name=new_name, department=new_dept, profile_status=new_status)
    print(f"\n  {G}✅  Employee updated.{R}")
    pause()


def delete_employee(db: EmployeeDatabase) -> None:
    clr(); header()
    print(f"  {B}DELETE EMPLOYEE{R}\n")
    emp_id = prompt("Employee ID to delete")
    emp = db.get(emp_id)
    if not emp:
        print(f"  {RE}Employee '{emp_id}' not found.{R}")
        pause(); return

    confirm = prompt(f"Delete {emp.name}? (yes/no)", "no")
    if confirm.lower() == "yes":
        db.delete(emp_id)
        print(f"  {G}✅  {emp.name} removed.{R}")
    else:
        print(f"  {GR}Cancelled.{R}")
    pause()


def search_employees(db: EmployeeDatabase) -> None:
    clr(); header()
    print(f"  {B}SEARCH EMPLOYEES{R}\n")
    query = prompt("Search (name / ID / department)")
    results = db.search(query)
    if not results:
        print(f"  {RE}No results for '{query}'.{R}")
    else:
        print(f"\n  Found {len(results)} result(s):\n")
        for e in results:
            flag = f"  {Y}🎉{R}" if e.is_birthday_today else ""
            print(
                f"  {G}{e.employee_id}{R}  {e.name:<22} {e.department:<14} "
                f"{e.date_of_birth.strftime('%d %b %Y')}  Age {e.age}{flag}"
            )
    pause()


def view_todays_birthdays(db: EmployeeDatabase, notifier: NotificationManager) -> None:
    clr(); header()
    print(f"  {B}TODAY'S BIRTHDAYS{R}\n")
    bdays = db.birthdays_today()
    if not bdays:
        print(f"  {GR}No birthdays today. 😢{R}")
    else:
        for e in bdays:
            print(f"  {Y}🎉  {e.name}  ({e.department})  —  turning {e.age} today!{R}")
        print()
        send = prompt("Send notifications now? (yes/no)", "yes")
        if send.lower() == "yes":
            notifier.notify_all_birthdays(bdays)
    pause()


def run_reports(db: EmployeeDatabase) -> None:
    clr(); header()
    choice = choose("Select Report", [
        "Monthly Birthday Report (current month)",
        "Annual Distribution",
        "Upcoming Birthdays (next 30 days)",
        "Back",
    ])
    if "Monthly" in choice:
        print(monthly_birthday_report(db))
    elif "Annual" in choice:
        print(annual_birthday_report(db))
    elif "Upcoming" in choice:
        print(upcoming_report(db, days=30))
    if "Back" not in choice:
        pause()


def configure_notifications(notifier: NotificationManager) -> None:
    clr(); header()
    print(f"  {B}NOTIFICATION CHANNELS{R}\n")
    print("  To activate a channel, set the corresponding environment variable:\n")
    channels = [
        ("Console",       "Always active — no configuration needed.", ""),
        ("Email (SMTP)",  "SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, HR_EMAIL, TEAM_EMAIL",
                          os.getenv("SMTP_USER", "")),
        ("Microsoft Teams","TEAMS_WEBHOOK_URL",
                          "✅ configured" if os.getenv("TEAMS_WEBHOOK_URL") else "⚠  not set"),
        ("Slack",         "SLACK_WEBHOOK_URL",
                          "✅ configured" if os.getenv("SLACK_WEBHOOK_URL") else "⚠  not set"),
    ]
    for name, note, status in channels:
        indicator = f"  {G}[active]{R}" if status in ("", "✅ configured") else f"  {RE}[inactive]{R}"
        print(f"  {B}{name}{R}{indicator}")
        print(f"    {GR}{note}{R}")
        if status and "configured" not in status and status != "":
            print(f"    Status: {status}")
        print()
    pause()


# ── Main menu ─────────────────────────────────────────────────────────────────

def main_menu(db: EmployeeDatabase, notifier: NotificationManager) -> None:
    while True:
        clr(); header()

        # Birthday banner
        bdays = db.birthdays_today()
        if bdays:
            names = ", ".join(e.name for e in bdays)
            print(f"  {Y}{B}🎉  Today's Birthday(s): {names}{R}\n")

        print(f"  {B}MAIN MENU{R}\n")
        options = [
            f"{G}1.{R}  View All Employees",
            f"{G}2.{R}  Add Employee",
            f"{G}3.{R}  Update Employee",
            f"{G}4.{R}  Delete Employee",
            f"{G}5.{R}  Search Employees",
            f"{G}6.{R}  Today's Birthdays  {Y}{'🎉 ' + str(len(bdays)) + ' birthday(s)!' if bdays else ''}{R}",
            f"{G}7.{R}  Run Daily Check Now",
            f"{G}8.{R}  Reports",
            f"{G}9.{R}  Notification Channel Status",
            f"{RE}0.{R}  Exit",
        ]
        for o in options:
            print(f"    {o}")

        choice = input(f"\n  {C}Select option: {R}").strip()

        if   choice == "1": view_all_employees(db)
        elif choice == "2": add_employee(db)
        elif choice == "3": update_employee(db)
        elif choice == "4": delete_employee(db)
        elif choice == "5": search_employees(db)
        elif choice == "6": view_todays_birthdays(db, notifier)
        elif choice == "7":
            daily_check(db, notifier, verbose=True)
            pause()
        elif choice == "8": run_reports(db)
        elif choice == "9": configure_notifications(notifier)
        elif choice == "0":
            print(f"\n  {GR}Goodbye! 👋{R}\n")
            sys.exit(0)
        else:
            print(f"  {RE}Invalid option.{R}")
            time.sleep(0.8)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Build notification manager
    notifier = NotificationManager(channels=[
        ConsoleNotifier(),
        EmailNotifier(),
        TeamsNotifier(),
        SlackNotifier(),
    ])

    # Load / initialise database
    db = EmployeeDatabase()

    # Run startup daily check
    daily_check(db, notifier, verbose=True)

    # Schedule background daily checks
    schedule_daily_check(db, notifier)

    # Launch interactive menu
    main_menu(db, notifier)


if __name__ == "__main__":
    main()
