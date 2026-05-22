# 🎂 Employee Birthday Notification System

A Python application that automatically detects employee birthdays and
broadcasts notifications across Console, Email, Microsoft Teams, and Slack.

---

## Project Structure

```
birthday_system/
├── main.py            # Interactive CLI & scheduler entry point
├── models.py          # Employee data model + JSON database
├── notifications.py   # Console / Email / Teams / Slack notifiers
├── reports.py         # Monthly, annual, upcoming reports
├── scheduler.py       # Standalone script for cron / Task Scheduler
├── requirements.txt   # Optional pip packages
└── employees.json     # Auto-created on first run (persisted data)
```

---

## Quick Start

```bash
# 1. Clone / copy the birthday_system/ folder
cd birthday_system

# 2. (Optional) install extras
pip install -r requirements.txt

# 3. Run the interactive CLI
python main.py
```

On first launch the app seeds 10 demo employees — two of them always have
today's birthday so you can see notifications immediately.

---

## Interactive Menu

| Option | Action |
|--------|--------|
| 1 | View all employees in a formatted table |
| 2 | Add a new employee |
| 3 | Update name / department / status |
| 4 | Delete an employee |
| 5 | Search by name, ID, or department |
| 6 | See today's birthday celebrants & send wishes |
| 7 | Run the daily check manually |
| 8 | Reports (monthly / annual / upcoming) |
| 9 | Notification channel status |
| 0 | Exit |

---

## Notification Channels

### Console (always on)
No configuration needed. Birthday alerts print to stdout in colour.

### Email (SMTP)
Set these environment variables:

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=hr@company.com
export SMTP_PASS=your_app_password
export HR_EMAIL=hr@company.com          # sender address
export TEAM_EMAIL=team@company.com      # mailing list / DL
```

### Microsoft Teams
1. Create an **Incoming Webhook** connector in your Teams channel.
2. Copy the webhook URL and set:

```bash
export TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/…
```

### Slack
1. Create an **Incoming Webhook** app in your Slack workspace.
2. Copy the webhook URL and set:

```bash
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/…
```

---

## Automated Daily Check (Cron)

Add to crontab to run at 09:00 every day:

```cron
0 9 * * * /usr/bin/python3 /absolute/path/birthday_system/scheduler.py
```

Windows Task Scheduler equivalent:
- Program: `python`
- Arguments: `C:\path\birthday_system\scheduler.py`
- Trigger: Daily at 09:00

Logs are written to `birthday_check.log` beside the script.

---

## Extending the System

| Goal | Where to edit |
|------|---------------|
| Add a new notification channel | Create a class in `notifications.py` with `send_birthday_alert` + `send_team_greeting`, then register it in `NotificationManager` inside `main.py` |
| Connect to a real database (PostgreSQL, MySQL) | Replace `EmployeeDatabase._save` / `_load` in `models.py` with SQLAlchemy or psycopg2 calls |
| REST API | Wrap `EmployeeDatabase` with FastAPI or Flask routes |
| Google Chat | Follow the same pattern as `TeamsNotifier` using Google Chat webhook JSON format |

---

## Security Notes

- Employee data is stored locally in `employees.json`. Restrict file permissions in production.
- SMTP credentials and webhook URLs are read from environment variables — never hard-code them.
- In a production deployment, store secrets in a vault (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault).
