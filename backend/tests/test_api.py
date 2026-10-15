"""Light end-to-end API tests (auth + CRUD flow)."""


def auth(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


PAYLOAD = {
    "full_name": "Asha Verma", "email": "asha@example.com", "phone": "+91 98765 43210",
    "department": "Engineering", "designation": "Engineer",
    "date_of_joining": "2024-01-10", "salary": 600000, "status": "Active",
}


def test_requires_authentication(client):
    assert client.get("/api/employees").status_code == 401


def test_bad_login(client):
    assert client.post("/api/auth/login", json={"username": "x", "password": "y"}).status_code == 401


def test_full_crud_flow(client):
    h = auth(client)
    created = client.post("/api/employees", json=PAYLOAD, headers=h)
    assert created.status_code == 201
    pk = created.json()["id"]
    assert created.json()["employee_id"] == "EMP0001"

    assert client.post("/api/employees", json=PAYLOAD, headers=h).status_code == 409

    got = client.get(f"/api/employees/{pk}", headers=h)
    assert got.json()["email"] == "asha@example.com"

    upd = client.put(f"/api/employees/{pk}", json={**PAYLOAD, "designation": "Lead"}, headers=h)
    assert upd.json()["designation"] == "Lead"

    listing = client.get("/api/employees", params={"search": "asha", "status": "Active"}, headers=h).json()
    assert listing["total"] == 1 and listing["total_pages"] == 1

    csv_resp = client.get("/api/employees/export/csv", headers=h)
    assert csv_resp.headers["content-type"].startswith("text/csv")

    assert client.get("/api/departments", headers=h).json() == ["Engineering"]
    assert client.delete(f"/api/employees/{pk}", headers=h).status_code == 204
    assert client.get(f"/api/employees/{pk}", headers=h).status_code == 404


def test_validation_error_returns_422(client):
    h = auth(client)
    assert client.post("/api/employees", json={**PAYLOAD, "salary": -1}, headers=h).status_code == 422
