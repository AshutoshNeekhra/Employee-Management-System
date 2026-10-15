import enum
from datetime import date

from sqlalchemy import Date, Enum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class EmploymentStatus(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(25))
    department: Mapped[str] = mapped_column(String(80), index=True)
    designation: Mapped[str] = mapped_column(String(80))
    date_of_joining: Mapped[date] = mapped_column(Date)
    salary: Mapped[float] = mapped_column(Numeric(12, 2, asdecimal=False))
    status: Mapped[EmploymentStatus] = mapped_column(
        Enum(
            EmploymentStatus,
            values_callable=lambda e: [m.value for m in e],
            name="employment_status",
        ),
        default=EmploymentStatus.ACTIVE,
        index=True,
    )
