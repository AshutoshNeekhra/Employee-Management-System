"""Insert sample data:  python seed.py"""
import random
from datetime import date, timedelta

from app.database import Base, SessionLocal, engine
from app.models import EmploymentStatus
from app.schemas import EmployeeCreate
from app.services import DuplicateError, EmployeeService

FIRST = ["Asha", "Rohan", "Priya", "Karan", "Neha", "Vikram", "Sneha", "Arjun", "Divya", "Manoj"]
LAST = ["Verma", "Sharma", "Iyer", "Reddy", "Patel", "Nair", "Gupta", "Joshi", "Rao", "Singh"]
DEPTS = ["Engineering", "HR", "Finance", "Sales", "Marketing", "Operations"]
ROLES = ["Associate", "Engineer", "Senior Engineer", "Manager", "Analyst", "Lead"]


def main(count: int = 25) -> None:
    Base.metadata.create_all(bind=engine)
    random.seed(42)
    with SessionLocal() as db:
        svc = EmployeeService(db)
        added = 0
        for i in range(count):
            first, last = random.choice(FIRST), random.choice(LAST)
            try:
                svc.create(EmployeeCreate(
                    full_name=f"{first} {last}",
                    email=f"{first}.{last}{i}@example.com",
                    phone=f"+91 9{random.randint(100000000, 999999999)}",
                    department=random.choice(DEPTS),
                    designation=random.choice(ROLES),
                    date_of_joining=date.today() - timedelta(days=random.randint(30, 1800)),
                    salary=random.randrange(300000, 2000000, 10000),
                    status=random.choice([EmploymentStatus.ACTIVE] * 4 + [EmploymentStatus.INACTIVE]),
                ))
                added += 1
            except DuplicateError:
                pass
    print(f"Seeded {added} employees")


if __name__ == "__main__":
    main()
