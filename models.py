"""
models.py — Employee data model and in-memory database
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import json
import os

DEPARTMENTS = [
    "Engineering", "Marketing", "Sales", "HR",
    "Finance", "Design", "Operations", "Product"
]

STATUS_OPTIONS = ["Online", "Away", "Offline"]


@dataclass
class Employee:
    employee_id: str
    name: str
    date_of_birth: date
    department: str
    profile_status: str = "Online"

    # ── computed properties ──────────────────────────────────────────────────

    @property
    def age(self) -> int:
        today = date.today()
        born  = self.date_of_birth
        return today.year - born.year - (
            (today.month, today.day) < (born.month, born.day)
        )

    @property
    def is_birthday_today(self) -> bool:
        today = date.today()
        return (
            self.date_of_birth.month == today.month
            and self.date_of_birth.day == today.day
        )

    @property
    def days_until_birthday(self) -> int:
        today = date.today()
        bday  = self.date_of_birth
        next_bday = date(today.year, bday.month, bday.day)
        if next_bday < today:
            next_bday = date(today.year + 1, bday.month, bday.day)
        return (next_bday - today).days

    # ── serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "employee_id":    self.employee_id,
            "name":           self.name,
            "date_of_birth":  self.date_of_birth.isoformat(),
            "department":     self.department,
            "profile_status": self.profile_status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Employee":
        return cls(
            employee_id    = data["employee_id"],
            name           = data["name"],
            date_of_birth  = date.fromisoformat(data["date_of_birth"]),
            department     = data["department"],
            profile_status = data.get("profile_status", "Online"),
        )


class EmployeeDatabase:
    """Simple JSON-backed employee store."""

    DB_FILE = "employees.json"

    def __init__(self):
        self._employees: dict[str, Employee] = {}
        self._load()
        if not self._employees:
            self._seed()

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def add(self, emp: Employee) -> None:
        if emp.employee_id in self._employees:
            raise ValueError(f"Employee ID '{emp.employee_id}' already exists.")
        self._employees[emp.employee_id] = emp
        self._save()

    def get(self, employee_id: str) -> Optional[Employee]:
        return self._employees.get(employee_id)

    def update(self, employee_id: str, **kwargs) -> Employee:
        emp = self._employees.get(employee_id)
        if not emp:
            raise KeyError(f"Employee '{employee_id}' not found.")
        for k, v in kwargs.items():
            if k == "date_of_birth" and isinstance(v, str):
                v = date.fromisoformat(v)
            setattr(emp, k, v)
        self._save()
        return emp

    def delete(self, employee_id: str) -> None:
        if employee_id not in self._employees:
            raise KeyError(f"Employee '{employee_id}' not found.")
        del self._employees[employee_id]
        self._save()

    def all(self) -> list[Employee]:
        return list(self._employees.values())

    # ── queries ───────────────────────────────────────────────────────────────

    def birthdays_today(self) -> list[Employee]:
        return [e for e in self._employees.values() if e.is_birthday_today]

    def birthdays_this_month(self) -> list[Employee]:
        month = date.today().month
        return sorted(
            [e for e in self._employees.values()
             if e.date_of_birth.month == month],
            key=lambda e: e.date_of_birth.day,
        )

    def upcoming_birthdays(self, days: int = 30) -> list[Employee]:
        return sorted(
            [e for e in self._employees.values()
             if 0 < e.days_until_birthday <= days],
            key=lambda e: e.days_until_birthday,
        )

    def by_department(self, dept: str) -> list[Employee]:
        return [e for e in self._employees.values() if e.department == dept]

    def search(self, query: str) -> list[Employee]:
        q = query.lower()
        return [
            e for e in self._employees.values()
            if q in e.name.lower()
            or q in e.employee_id.lower()
            or q in e.department.lower()
        ]

    # ── persistence ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        with open(self.DB_FILE, "w") as f:
            json.dump([e.to_dict() for e in self._employees.values()], f, indent=2)

    def _load(self) -> None:
        if os.path.exists(self.DB_FILE):
            with open(self.DB_FILE) as f:
                for d in json.load(f):
                    emp = Employee.from_dict(d)
                    self._employees[emp.employee_id] = emp

    def _seed(self) -> None:
        today = date.today()
        seed_data = [
            ("E001", "Priya Sharma",  today.replace(year=1992),          "Engineering", "Online"),
            ("E002", "Rahul Mehta",   date(1988,  3, 15),                "Marketing",   "Away"),
            ("E003", "Aisha Bano",    date(1995,  7, 22),                "HR",          "Online"),
            ("E004", "Vikram Singh",  date(1990, 11,  8),                "Sales",       "Offline"),
            ("E005", "Neha Reddy",    today.replace(year=1993),          "Design",      "Online"),
            ("E006", "Suresh Kumar",  date(1985,  1, 30),                "Finance",     "Online"),
            ("E007", "Divya Nair",    date(1997,  9, 12),                "Product",     "Away"),
            ("E008", "Ankit Joshi",   date(1991, 12,  5),                "Engineering", "Online"),
            ("E009", "Meera Iyer",    date(1994,  6, 18),                "Operations",  "Offline"),
            ("E010", "Ravi Teja",     date(1989,  2, 14),                "Sales",       "Online"),
        ]
        for eid, name, dob, dept, status in seed_data:
            self._employees[eid] = Employee(eid, name, dob, dept, status)
        self._save()
