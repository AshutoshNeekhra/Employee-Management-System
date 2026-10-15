# Employee Management System

Admin web app for managing employee records (full CRUD, search, filters, pagination, CSV export).

| Layer     | Technology                                   |
|-----------|----------------------------------------------|
| Frontend  | Streamlit                                    |
| Backend   | Python 3.10+, FastAPI, SQLAlchemy 2          |
| Database  | SQLite (default) · PostgreSQL via Docker/`DATABASE_URL` |
| API docs  | Swagger UI (`/docs`) / OpenAPI (`/openapi.json`) |
| Tests     | pytest (+ `unittest.mock`), FastAPI TestClient |

## Features
- Add / view / edit / delete (with confirmation) / list employees
- Search by name or email, filter by department and status, pagination
- Employee fields: Employee ID (auto `EMP0001`…), Full Name, Email, Phone, Department, Designation, Date of Joining, Salary, Status (Active/Inactive)
- Validation: email & phone format, positive salary, no future joining date, unique email / employee ID (HTTP 409 on duplicates)
- **Bonus:** login with token auth · department listing/selection · CSV export · Docker Compose · seed script

## Project layout
```
backend/   FastAPI app (app/), tests/, seed.py, Dockerfile
frontend/  Streamlit app (app.py), Dockerfile
scripts/schema.sql        reference PostgreSQL schema
docker-compose.yml        db + backend + frontend
postman_collection.json   sample API requests
```

## Prerequisites
- Python 3.10+ and pip  (or Docker + Docker Compose)

## Option A – Run locally (SQLite, zero config)
```bash
# 1. Backend  (terminal 1)
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                                         # optional: 25 sample employees
uvicorn app.main:app --reload --port 8000

# 2. Frontend (terminal 2)
cd frontend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
- App: http://localhost:8501  — login **admin / admin123**
- Swagger UI: http://localhost:8000/docs  (log in via `POST /api/auth/login`, then click *Authorize*)

## Option B – Docker Compose (PostgreSQL)
```bash
docker compose up --build
# optional sample data:
docker compose exec backend python seed.py
```
App on http://localhost:8501, API docs on http://localhost:8000/docs.

## Configuration (environment variables)
| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./employees.db` | e.g. `postgresql+psycopg2://user:pass@host:5432/db` or `mysql+pymysql://…` (install `pymysql`) |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | `admin` / `admin123` | login credentials |
| `SECRET_KEY` | `change-me-in-production` | token signing key |
| `BACKEND_URL` (frontend) | `http://localhost:8000` | where Streamlit finds the API |

Tables are created automatically on backend start-up. `scripts/schema.sql` is provided for manual PostgreSQL setup.

## Run the tests
```bash
cd backend
pytest -v
```
Service-layer unit tests (`tests/test_employee_service.py`) use an in-memory SQLite DB plus one mock-based test; `tests/test_api.py` covers auth and the CRUD flow end to end.

## REST API
All `/api/employees*` and `/api/departments` routes require `Authorization: Bearer <token>`.

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/login` | `{username, password}` → `{access_token}` |
| GET | `/api/employees?search=&department=&status=&page=1&page_size=10` | paginated list |
| POST | `/api/employees` | create (201) |
| GET | `/api/employees/{id}` | details |
| PUT | `/api/employees/{id}` | update |
| DELETE | `/api/employees/{id}` | delete (204) |
| GET | `/api/employees/export/csv` | CSV (same filters) |
| GET | `/api/departments` | distinct departments |
| GET | `/health` | liveness |

Sample requests: import `postman_collection.json` (run **Login** first; it stores the token), or:
```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -X POST localhost:8000/api/employees -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{
  "full_name":"Asha Verma","email":"asha.verma@example.com","phone":"+91 98765 43210",
  "department":"Engineering","designation":"Software Engineer",
  "date_of_joining":"2024-06-17","salary":850000,"status":"Active"}'

curl "localhost:8000/api/employees?search=asha&status=Active&page=1&page_size=10" -H "Authorization: Bearer $TOKEN"
```

## Design notes
- **Layers:** routers (HTTP) → `EmployeeService` (business rules, no HTTP) → SQLAlchemy models. Errors are domain exceptions mapped to 404/409 centrally.
- **Auth:** single admin from env vars with HMAC-signed, expiring tokens (kept dependency-free for the assessment; use a user table + hashed passwords + JWT library in production).
