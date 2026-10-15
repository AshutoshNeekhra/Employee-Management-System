# Employee Management System

A simple web application to manage employee records. It allows an administrator to add, view, update, search, filter, and delete employee information.

## Features

- Admin login
- Add, view, edit, and delete employees
- Search employees by name or email
- Filter employees by department and employment status
- Pagination for employee records
- Export employee data to CSV
- REST APIs for employee management
- Database integration
- Automated backend tests
- Docker Compose configuration

## Technologies Used

- **Frontend:** Streamlit
- **Backend:** Python, FastAPI
- **Database:** SQLite (default) and PostgreSQL (optional)
- **ORM:** SQLAlchemy
- **Testing:** Pytest
- **API Documentation:** Swagger UI
- **Tools:** Git, Docker, Postman

## Project Structure

```
Employee-Management-System/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── services.py
│   ├── tests/
│   ├── requirements.txt
│   └── seed.py
├── frontend/
│   ├── app.py
│   └── requirements.txt
├── scripts/
│   └── schema.sql
├── docker-compose.yml
├── postman_collection.json
└── README.md
```

## Requirements

- Python 3.11 or a compatible version
- Git
- A terminal such as PowerShell

## How to Run the Project

### 1. Clone the repository

```
git clone https://github.com/AshutoshNeekhra/Employee-Management-System.git
cd Employee-Management-System
```

### 2. Start the backend

Open a terminal in the project folder and run:

```
cd backend
python -m venv .venv
```

Install the dependencies:

```
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the API:

```
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

The backend will run at: `http://localhost:8000`

Open the API documentation at: `http://localhost:8000/docs`

### 3. Start the frontend

Open a second terminal in the project folder and run:

```
cd frontend
python -m venv .venv
```

Install the frontend dependencies:

```
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start Streamlit:

```
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL displayed in your terminal, usually: `http://localhost:8501`

Keep both terminals running while using the application.

## Demo Login

For local demonstration, the default credentials are:

- **Username:** `admin`
- **Password:** `admin123`

Change the default credentials before exposing the application publicly.

## Running Tests

Open a terminal in the project folder and run:

```
cd backend
.\.venv\Scripts\python.exe -m pytest
```

## API Collection

The file `postman_collection.json` contains sample API requests that can be imported into Postman for testing.

## Database

SQLite is used by default, so the application can run locally without installing a separate database server. PostgreSQL configuration is also provided for use with Docker Compose.

## Author

**Ashutosh Neekhra**
GitHub: [AshutoshNeekhra](https://github.com/AshutoshNeekhra)

## License

This project was developed for learning and demonstration purposes.
