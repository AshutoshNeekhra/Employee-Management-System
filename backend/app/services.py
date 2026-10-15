"""Service layer: all business rules live here (unit-tested without HTTP)."""
import csv
import io
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Employee, EmploymentStatus
from .schemas import EmployeeCreate, EmployeeUpdate

CSV_COLUMNS = [
    "employee_id", "full_name", "email", "phone", "department",
    "designation", "date_of_joining", "salary", "status",
]


class NotFoundError(Exception):
    """Requested employee does not exist."""


class DuplicateError(Exception):
    """Email or employee ID already in use."""


class EmployeeService:
    def __init__(self, db: Session):
        self.db = db

    # ---- helpers -------------------------------------------------------
    def _email_taken(self, email: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(Employee.id).where(func.lower(Employee.email) == email.lower())
        if exclude_id is not None:
            stmt = stmt.where(Employee.id != exclude_id)
        return self.db.execute(stmt).first() is not None

    def _employee_id_taken(self, employee_id: str) -> bool:
        stmt = select(Employee.id).where(Employee.employee_id == employee_id)
        return self.db.execute(stmt).first() is not None

    def _next_employee_id(self) -> str:
        n = (self.db.execute(select(func.max(Employee.id))).scalar() or 0) + 1
        while self._employee_id_taken(f"EMP{n:04d}"):
            n += 1
        return f"EMP{n:04d}"

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateError("An employee with the same email or employee ID already exists") from exc

    def _filtered(self, search, department, status):
        stmt = select(Employee)
        if search and search.strip():
            like = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(func.lower(Employee.full_name).like(like), func.lower(Employee.email).like(like))
            )
        if department and department.strip():
            stmt = stmt.where(func.lower(Employee.department) == department.strip().lower())
        if status is not None:
            stmt = stmt.where(Employee.status == status)
        return stmt

    # ---- CRUD ----------------------------------------------------------
    def create(self, data: EmployeeCreate) -> Employee:
        if self._email_taken(data.email):
            raise DuplicateError(f"Email '{data.email}' is already registered")
        employee_id = data.employee_id
        if employee_id:
            if self._employee_id_taken(employee_id):
                raise DuplicateError(f"Employee ID '{employee_id}' already exists")
        else:
            employee_id = self._next_employee_id()
        emp = Employee(employee_id=employee_id, **data.model_dump(exclude={"employee_id"}))
        self.db.add(emp)
        self._commit()
        self.db.refresh(emp)
        return emp

    def get(self, pk: int) -> Employee:
        emp = self.db.get(Employee, pk)
        if emp is None:
            raise NotFoundError(f"Employee {pk} not found")
        return emp

    def update(self, pk: int, data: EmployeeUpdate) -> Employee:
        emp = self.get(pk)
        if self._email_taken(data.email, exclude_id=pk):
            raise DuplicateError(f"Email '{data.email}' is already registered")
        for field, value in data.model_dump().items():
            setattr(emp, field, value)
        self._commit()
        self.db.refresh(emp)
        return emp

    def delete(self, pk: int) -> None:
        emp = self.get(pk)
        self.db.delete(emp)
        self.db.commit()

    def list_employees(
        self,
        search: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[EmploymentStatus] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Employee], int]:
        if page < 1 or page_size < 1:
            raise ValueError("page and page_size must be >= 1")
        base = self._filtered(search, department, status)
        total = self.db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
        items = (
            self.db.execute(base.order_by(Employee.id).offset((page - 1) * page_size).limit(page_size))
            .scalars()
            .all()
        )
        return list(items), total

    def departments(self) -> List[str]:
        rows = self.db.execute(select(Employee.department).distinct().order_by(Employee.department))
        return [r[0] for r in rows]

    def export_csv(self, search=None, department=None, status=None) -> str:
        stmt = self._filtered(search, department, status).order_by(Employee.id)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(CSV_COLUMNS)
        for e in self.db.execute(stmt).scalars():
            writer.writerow([
                e.employee_id, e.full_name, e.email, e.phone, e.department, e.designation,
                e.date_of_joining.isoformat(), f"{e.salary:.2f}", e.status.value,
            ])
        return buf.getvalue()
