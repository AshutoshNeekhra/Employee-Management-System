import math
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from ..auth import require_auth
from ..database import get_db
from ..models import EmploymentStatus
from ..schemas import EmployeeCreate, EmployeeOut, EmployeePage, EmployeeUpdate
from ..services import EmployeeService

router = APIRouter(prefix="/api/employees", tags=["Employees"], dependencies=[Depends(require_auth)])
departments_router = APIRouter(prefix="/api/departments", tags=["Departments"], dependencies=[Depends(require_auth)])


def get_service(db: Session = Depends(get_db)) -> EmployeeService:
    return EmployeeService(db)


@router.get("", response_model=EmployeePage, summary="List employees (search, filter, paginate)")
def list_employees(
    search: Optional[str] = Query(None, description="Matches name or email (case-insensitive)"),
    department: Optional[str] = Query(None),
    status_: Optional[EmploymentStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    svc: EmployeeService = Depends(get_service),
):
    items, total = svc.list_employees(search, department, status_, page, page_size)
    return EmployeePage(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/export/csv", summary="Export (filtered) employees as CSV")
def export_csv(
    search: Optional[str] = None,
    department: Optional[str] = None,
    status_: Optional[EmploymentStatus] = Query(None, alias="status"),
    svc: EmployeeService = Depends(get_service),
):
    content = svc.export_csv(search, department, status_)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="employees.csv"'},
    )


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED, summary="Create an employee")
def create_employee(body: EmployeeCreate, svc: EmployeeService = Depends(get_service)):
    return svc.create(body)


@router.get("/{pk}", response_model=EmployeeOut, summary="Get one employee")
def get_employee(pk: int, svc: EmployeeService = Depends(get_service)):
    return svc.get(pk)


@router.put("/{pk}", response_model=EmployeeOut, summary="Update an employee")
def update_employee(pk: int, body: EmployeeUpdate, svc: EmployeeService = Depends(get_service)):
    return svc.update(pk, body)


@router.delete("/{pk}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an employee")
def delete_employee(pk: int, svc: EmployeeService = Depends(get_service)):
    svc.delete(pk)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@departments_router.get("", response_model=List[str], summary="Distinct departments in use")
def list_departments(svc: EmployeeService = Depends(get_service)):
    return svc.departments()
