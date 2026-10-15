"""Employee Management System - Streamlit frontend (talks to the FastAPI backend)."""
import os
from datetime import date

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
API = f"{BACKEND_URL}/api"
STATUSES = ["Active", "Inactive"]
PAGE_SIZES = [5, 10, 20, 50]
DEFAULT_DEPARTMENTS = ["Engineering", "HR", "Finance", "Sales", "Marketing", "Operations", "IT", "Support"]

st.set_page_config(page_title="Employee Management System", page_icon="👥", layout="wide")


# ----------------------------------------------------------------- state / helpers
def init_state():
    defaults = {
        "token": None, "page": "list", "selected_id": None,
        "list_page": 1, "confirm_delete_id": None, "flash": None, "csv": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def goto(page, employee_id=None):
    st.session_state.page = page
    st.session_state.selected_id = employee_id
    st.session_state.confirm_delete_id = None
    st.session_state.csv = None


def flash(kind, message):
    st.session_state.flash = (kind, message)


def show_flash():
    if st.session_state.flash:
        kind, message = st.session_state.flash
        getattr(st, kind)(message)
        st.session_state.flash = None


def error_text(resp):
    try:
        detail = resp.json().get("detail")
    except ValueError:
        return f"Request failed (HTTP {resp.status_code})"
    if isinstance(detail, list):
        parts = []
        for d in detail:
            field = ".".join(str(p) for p in d.get("loc", [])[1:])
            parts.append(f"{field}: {d.get('msg')}")
        return "; ".join(parts)
    return str(detail)


def api(method, path, **kwargs):
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
    try:
        resp = requests.request(method, f"{API}{path}", headers=headers, timeout=15, **kwargs)
    except requests.RequestException:
        st.error(f"Cannot reach the backend at {BACKEND_URL}. Is the API running?")
        return None
    if resp.status_code == 401 and st.session_state.token:
        st.session_state.token = None
        flash("warning", "Your session expired. Please sign in again.")
        st.rerun()
    return resp


def fetch_departments():
    resp = api("GET", "/departments")
    return resp.json() if resp is not None and resp.ok else []


def reset_list_page():
    st.session_state.list_page = 1


def change_list_page(delta):
    st.session_state.list_page += delta


def request_delete(employee_id):
    st.session_state.confirm_delete_id = employee_id
    st.session_state.page = "list"
    st.session_state.csv = None


def cancel_delete():
    st.session_state.confirm_delete_id = None


def logout():
    for key in ("token", "selected_id", "confirm_delete_id", "csv"):
        st.session_state[key] = None
    st.session_state.page = "list"


# ----------------------------------------------------------------- views
def login_view():
    st.title("👥 Employee Management System")
    show_flash()
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.form("login"):
            st.subheader("Admin sign in")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        st.caption("Default demo credentials: admin / admin123")
    if submitted:
        resp = api("POST", "/auth/login", json={"username": username, "password": password})
        if resp is not None and resp.ok:
            st.session_state.token = resp.json()["access_token"]
            st.rerun()
        elif resp is not None:
            st.error(error_text(resp))


def confirm_delete_panel():
    emp_id = st.session_state.confirm_delete_id
    resp = api("GET", f"/employees/{emp_id}")
    if resp is None or not resp.ok:
        st.session_state.confirm_delete_id = None
        return
    emp = resp.json()
    with st.container(border=True):
        st.warning(f"Delete **{emp['full_name']}** ({emp['employee_id']})? This cannot be undone.")
        c1, c2, _ = st.columns([1, 1, 4])
        if c1.button("Yes, delete", type="primary", key="confirm_yes"):
            r = api("DELETE", f"/employees/{emp_id}")
            if r is not None and r.status_code == 204:
                flash("success", f"Deleted {emp['full_name']}.")
            elif r is not None:
                flash("error", error_text(r))
            st.session_state.confirm_delete_id = None
            st.rerun()
        c2.button("Cancel", key="confirm_no", on_click=cancel_delete)


def list_view():
    st.header("Employees")
    show_flash()
    if st.session_state.confirm_delete_id:
        confirm_delete_panel()

    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    search = c1.text_input("Search by name or email", key="f_search", on_change=reset_list_page)
    department = c2.selectbox("Department", ["All"] + fetch_departments(), key="f_dept", on_change=reset_list_page)
    status = c3.selectbox("Status", ["All"] + STATUSES, key="f_status", on_change=reset_list_page)
    page_size = c4.selectbox("Per page", PAGE_SIZES, index=1, key="f_size", on_change=reset_list_page)

    params = {"page": st.session_state.list_page, "page_size": page_size}
    filters = {}
    if search.strip():
        filters["search"] = search.strip()
    if department != "All":
        filters["department"] = department
    if status != "All":
        filters["status"] = status
    resp = api("GET", "/employees", params={**params, **filters})
    if resp is None:
        return
    if not resp.ok:
        st.error(error_text(resp))
        return
    data = resp.json()

    # e.g. last row of the last page was deleted
    if data["total_pages"] and st.session_state.list_page > data["total_pages"]:
        st.session_state.list_page = data["total_pages"]
        st.rerun()

    top_l, top_r = st.columns([4, 2])
    top_l.caption(f"{data['total']} employee(s) found")
    with top_r:
        if st.button("Prepare CSV export"):
            r = api("GET", "/employees/export/csv", params=filters)
            if r is not None and r.ok:
                st.session_state.csv = r.content
        if st.session_state.csv:
            st.download_button("⬇ Download employees.csv", st.session_state.csv,
                               file_name="employees.csv", mime="text/csv")

    if not data["items"]:
        st.info("No employees match your criteria.")
        return

    widths = [1.2, 2.2, 3, 2, 2.2, 1.2, 3]
    header = st.columns(widths)
    for col, label in zip(header, ["ID", "Name", "Email", "Department", "Designation", "Status", "Actions"]):
        col.markdown(f"**{label}**")
    st.divider()
    for emp in data["items"]:
        row = st.columns(widths)
        row[0].write(emp["employee_id"])
        row[1].write(emp["full_name"])
        row[2].write(emp["email"])
        row[3].write(emp["department"])
        row[4].write(emp["designation"])
        row[5].write("🟢 Active" if emp["status"] == "Active" else "🔴 Inactive")
        a, b, c = row[6].columns(3)
        a.button("View", key=f"view_{emp['id']}", on_click=goto, args=("details", emp["id"]))
        b.button("Edit", key=f"edit_{emp['id']}", on_click=goto, args=("edit", emp["id"]))
        c.button("Delete", key=f"del_{emp['id']}", on_click=request_delete, args=(emp["id"],))

    p1, p2, p3 = st.columns([1, 2, 1])
    p1.button("◀ Previous", disabled=st.session_state.list_page <= 1, on_click=change_list_page, args=(-1,))
    p2.markdown(
        f"<div style='text-align:center'>Page {data['page']} of {data['total_pages']}</div>",
        unsafe_allow_html=True,
    )
    p3.button("Next ▶", disabled=st.session_state.list_page >= data["total_pages"],
              on_click=change_list_page, args=(1,))


def details_view():
    resp = api("GET", f"/employees/{st.session_state.selected_id}")
    if resp is None:
        return
    if not resp.ok:
        st.error(error_text(resp))
        st.button("Back to list", on_click=goto, args=("list",))
        return
    emp = resp.json()
    st.header(emp["full_name"])
    show_flash()
    left, right = st.columns(2)
    left.markdown(f"**Employee ID:** {emp['employee_id']}")
    left.markdown(f"**Email:** {emp['email']}")
    left.markdown(f"**Phone:** {emp['phone']}")
    left.markdown(f"**Department:** {emp['department']}")
    right.markdown(f"**Designation:** {emp['designation']}")
    right.markdown(f"**Date of joining:** {emp['date_of_joining']}")
    right.markdown(f"**Salary:** {emp['salary']:,.2f}")
    right.markdown(f"**Status:** {'🟢 Active' if emp['status'] == 'Active' else '🔴 Inactive'}")
    st.divider()
    b1, b2, b3, _ = st.columns([1, 1, 1, 4])
    b1.button("← Back", on_click=goto, args=("list",))
    b2.button("Edit", on_click=goto, args=("edit", emp["id"]))
    b3.button("Delete", on_click=request_delete, args=(emp["id"],))


def employee_form(existing=None):
    e = existing or {}
    departments = sorted(set(DEFAULT_DEPARTMENTS) | set(fetch_departments()) | ({e["department"]} if e else set()))
    options = departments + ["Other…"]
    with st.form("employee_form"):
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Full name *", value=e.get("full_name", ""))
        email = c2.text_input("Email address *", value=e.get("email", ""))
        phone = c1.text_input("Phone number *", value=e.get("phone", ""), placeholder="+91 98765 43210")
        designation = c2.text_input("Designation *", value=e.get("designation", ""))
        current = e.get("department")
        dept_choice = c1.selectbox("Department *", options, index=options.index(current) if current in options else 0)
        custom_dept = c2.text_input("New department (only if 'Other…' selected)")
        joined = c1.date_input(
            "Date of joining *",
            value=date.fromisoformat(e["date_of_joining"]) if e else date.today(),
            min_value=date(1950, 1, 1), max_value=date.today(),
        )
        salary = c2.number_input("Salary *", min_value=0.0, step=1000.0, format="%.2f",
                                 value=float(e.get("salary", 0.0)))
        status = st.radio("Employment status", STATUSES, horizontal=True,
                          index=STATUSES.index(e.get("status", "Active")))
        submitted = st.form_submit_button("Save changes" if e else "Add employee", type="primary")

    if submitted:
        department = custom_dept.strip() if dept_choice == "Other…" else dept_choice
        if not department:
            st.error("Please enter a department name.")
            return
        payload = {
            "full_name": full_name, "email": email, "phone": phone, "department": department,
            "designation": designation, "date_of_joining": joined.isoformat(),
            "salary": salary, "status": status,
        }
        if e:
            resp = api("PUT", f"/employees/{e['id']}", json=payload)
        else:
            resp = api("POST", "/employees", json=payload)
        if resp is None:
            return
        if resp.ok:
            flash("success", "Employee updated." if e else "Employee added.")
            goto("details", resp.json()["id"])
            st.rerun()
        else:
            st.error(error_text(resp))


def add_view():
    st.header("Add employee")
    st.caption("Employee ID is generated automatically.")
    employee_form()
    st.button("Cancel", on_click=goto, args=("list",))


def edit_view():
    resp = api("GET", f"/employees/{st.session_state.selected_id}")
    if resp is None:
        return
    if not resp.ok:
        st.error(error_text(resp))
        st.button("Back to list", on_click=goto, args=("list",))
        return
    emp = resp.json()
    st.header(f"Edit {emp['full_name']} ({emp['employee_id']})")
    employee_form(emp)
    st.button("Cancel", on_click=goto, args=("details", emp["id"]))


# ----------------------------------------------------------------- main
init_state()
if not st.session_state.token:
    login_view()
    st.stop()

with st.sidebar:
    st.title("👥 EMS")
    st.button("Employees", use_container_width=True, on_click=goto, args=("list",))
    st.button("➕ Add employee", use_container_width=True, on_click=goto, args=("add",))
    st.divider()
    st.button("Sign out", use_container_width=True, on_click=logout)

{"list": list_view, "details": details_view, "add": add_view, "edit": edit_view}[st.session_state.page]()
