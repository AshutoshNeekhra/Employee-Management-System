"""Unit tests for the service layer (business logic)."""
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.models import EmploymentStatus
from app.schemas import EmployeeUpdate
from app.services import DuplicateError, EmployeeService, NotFoundError


def test_create_generates_sequential_employee_id(db, make_create):
    svc = EmployeeService(db)
    assert svc.create(make_create()).employee_id == "EMP0001"
    assert svc.create(make_create()).employee_id == "EMP0002"


def test_create_with_custom_employee_id_is_normalised(db, make_create):
    emp = EmployeeService(db).create(make_create(employee_id=" abc-1 "))
    assert emp.employee_id == "ABC-1"


def test_create_duplicate_custom_employee_id_rejected(db, make_create):
    svc = EmployeeService(db)
    svc.create(make_create(employee_id="X1"))
    with pytest.raises(DuplicateError):
        svc.create(make_create(employee_id="X1"))


def test_email_is_lowercased_and_duplicates_rejected_case_insensitively(db, make_create):
    svc = EmployeeService(db)
    emp = svc.create(make_create(email="Jane.Doe@Example.com"))
    assert emp.email == "jane.doe@example.com"
    with pytest.raises(DuplicateError):
        svc.create(make_create(email="JANE.DOE@example.com"))


def test_get_missing_raises_not_found(db):
    with pytest.raises(NotFoundError):
        EmployeeService(db).get(999)


def test_update_changes_fields(db, make_create):
    svc = EmployeeService(db)
    emp = svc.create(make_create())
    payload = EmployeeUpdate(**{**make_create().model_dump(exclude={"employee_id"}),
                                "email": emp.email, "designation": "Lead", "status": "Inactive"})
    updated = svc.update(emp.id, payload)
    assert updated.designation == "Lead"
    assert updated.status == EmploymentStatus.INACTIVE
    assert updated.employee_id == emp.employee_id  # never changes


def test_update_keeping_own_email_is_allowed(db, make_create):
    svc = EmployeeService(db)
    emp = svc.create(make_create())
    payload = EmployeeUpdate(**make_create(email=emp.email).model_dump(exclude={"employee_id"}))
    assert svc.update(emp.id, payload).email == emp.email


def test_update_to_another_employees_email_rejected(db, make_create):
    svc = EmployeeService(db)
    a, b = svc.create(make_create()), svc.create(make_create())
    payload = EmployeeUpdate(**make_create(email=a.email).model_dump(exclude={"employee_id"}))
    with pytest.raises(DuplicateError):
        svc.update(b.id, payload)


def test_update_missing_raises_not_found(db, make_create):
    payload = EmployeeUpdate(**make_create().model_dump(exclude={"employee_id"}))
    with pytest.raises(NotFoundError):
        EmployeeService(db).update(42, payload)


def test_delete_removes_employee(db, make_create):
    svc = EmployeeService(db)
    emp = svc.create(make_create())
    svc.delete(emp.id)
    with pytest.raises(NotFoundError):
        svc.get(emp.id)


def test_delete_missing_raises_not_found(db):
    with pytest.raises(NotFoundError):
        EmployeeService(db).delete(1)


def test_search_matches_name_or_email(db, make_create):
    svc = EmployeeService(db)
    svc.create(make_create(full_name="Asha Verma", email="asha@corp.com"))
    svc.create(make_create(full_name="Rohan Iyer", email="r.iyer@corp.com"))
    assert [e.full_name for e in svc.list_employees(search="ASHA")[0]] == ["Asha Verma"]
    assert [e.full_name for e in svc.list_employees(search="iyer@")[0]] == ["Rohan Iyer"]
    assert svc.list_employees(search="nobody")[1] == 0


def test_filter_by_department_and_status(db, make_create):
    svc = EmployeeService(db)
    svc.create(make_create(department="HR", status="Active"))
    svc.create(make_create(department="HR", status="Inactive"))
    svc.create(make_create(department="Sales", status="Active"))
    assert svc.list_employees(department="hr")[1] == 2
    assert svc.list_employees(status=EmploymentStatus.ACTIVE)[1] == 2
    assert svc.list_employees(department="HR", status=EmploymentStatus.INACTIVE)[1] == 1


def test_pagination_returns_slices_and_total(db, make_create):
    svc = EmployeeService(db)
    for _ in range(7):
        svc.create(make_create())
    page1, total = svc.list_employees(page=1, page_size=3)
    page3, _ = svc.list_employees(page=3, page_size=3)
    assert total == 7 and len(page1) == 3 and len(page3) == 1
    assert svc.list_employees(page=4, page_size=3)[0] == []


def test_invalid_pagination_arguments_rejected(db):
    with pytest.raises(ValueError):
        EmployeeService(db).list_employees(page=0)


def test_departments_are_distinct_and_sorted(db, make_create):
    svc = EmployeeService(db)
    for d in ["Sales", "HR", "Sales"]:
        svc.create(make_create(department=d))
    assert svc.departments() == ["HR", "Sales"]


def test_export_csv_has_header_and_filtered_rows(db, make_create):
    svc = EmployeeService(db)
    svc.create(make_create(department="HR"))
    svc.create(make_create(department="Sales"))
    lines = svc.export_csv(department="HR").strip().splitlines()
    assert lines[0].startswith("employee_id,full_name,email")
    assert len(lines) == 2 and "HR" in lines[1]


@pytest.mark.parametrize("override", [
    {"salary": 0},
    {"salary": -5},
    {"phone": "abc"},
    {"email": "not-an-email"},
    {"full_name": " "},
    {"date_of_joining": "2999-01-01"},
    {"status": "Retired"},
])
def test_validation_rejects_bad_input(make_create, override):
    with pytest.raises(ValidationError):
        make_create(**override)


def test_integrity_error_is_translated_and_rolled_back(make_create):
    """Mock-based test (Mockito equivalent): DB race on unique constraint."""
    db = MagicMock()
    db.execute.return_value.first.return_value = None
    db.execute.return_value.scalar.return_value = 0
    db.commit.side_effect = IntegrityError("stmt", {}, Exception("dup"))
    with pytest.raises(DuplicateError):
        EmployeeService(db).create(make_create())
    db.rollback.assert_called_once()
