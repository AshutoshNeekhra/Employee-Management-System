import re
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import EmploymentStatus

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-]{6,18}[0-9]$")


class EmployeeBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120, examples=["Asha Verma"])
    email: str = Field(max_length=255, examples=["asha.verma@example.com"])
    phone: str = Field(examples=["+91 98765 43210"])
    department: str = Field(min_length=1, max_length=80, examples=["Engineering"])
    designation: str = Field(min_length=1, max_length=80, examples=["Software Engineer"])
    date_of_joining: date = Field(examples=["2024-06-17"])
    salary: float = Field(gt=0, le=100_000_000, examples=[850000])
    status: EmploymentStatus = EmploymentStatus.ACTIVE

    @field_validator("full_name", "department", "designation", "phone", "email", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        if not EMAIL_RE.match(v):
            raise ValueError("invalid email address")
        return v.lower()

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        if not PHONE_RE.match(v):
            raise ValueError("invalid phone number (7-20 digits, optional leading +)")
        return v

    @field_validator("date_of_joining")
    @classmethod
    def _doj(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("date of joining cannot be in the future")
        return v


class EmployeeCreate(EmployeeBase):
    employee_id: Optional[str] = Field(
        default=None, max_length=20, description="Optional. Auto-generated (EMP0001...) if omitted."
    )

    @field_validator("employee_id", mode="before")
    @classmethod
    def _emp_id(cls, v):
        if isinstance(v, str):
            v = v.strip().upper()
            return v or None
        return v


class EmployeeUpdate(EmployeeBase):
    pass


class EmployeeOut(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: str


class EmployeePage(BaseModel):
    items: List[EmployeeOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
