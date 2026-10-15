-- Reference schema (PostgreSQL). The app also creates this automatically on startup via SQLAlchemy.
-- Usage:  psql -U emp -d employees -f scripts/schema.sql
CREATE TYPE employment_status AS ENUM ('Active', 'Inactive');

CREATE TABLE IF NOT EXISTS employees (
    id               SERIAL PRIMARY KEY,
    employee_id      VARCHAR(20)  NOT NULL UNIQUE,
    full_name        VARCHAR(120) NOT NULL,
    email            VARCHAR(255) NOT NULL UNIQUE,
    phone            VARCHAR(25)  NOT NULL,
    department       VARCHAR(80)  NOT NULL,
    designation      VARCHAR(80)  NOT NULL,
    date_of_joining  DATE         NOT NULL,
    salary           NUMERIC(12,2) NOT NULL CHECK (salary > 0),
    status           employment_status NOT NULL DEFAULT 'Active'
);

CREATE INDEX IF NOT EXISTS ix_employees_full_name  ON employees (full_name);
CREATE INDEX IF NOT EXISTS ix_employees_department ON employees (department);
CREATE INDEX IF NOT EXISTS ix_employees_status     ON employees (status);
