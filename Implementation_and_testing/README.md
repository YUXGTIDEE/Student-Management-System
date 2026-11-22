# Implementation and Testing

This directory contains the executable Django application, database
migrations, Docker configuration, source code, and automated tests for the
Student Management System.

For project-wide requirements, architecture, diagrams, and documentation,
see the [root README](../README.md).

## Technology

- Python 3.12
- Django 5.x
- MySQL 8.0
- pytest and pytest-django
- Docker Compose
- Gunicorn and WhiteNoise

## Main Features

- Login, logout, account locking, password management, and role-based
  authorization.
- Administrator, teacher, and student profiles.
- Course, semester, and course-section management.
- Student search and filtering.
- Course registration and cancellation.
- Grade entry, grade conversion, GPA calculation, and gradebook locking.
- Sample data generation and database migrations.

## Project Structure

| Directory | Purpose |
|---|---|
| `accounts/` | Authentication, roles, accounts, and sample data |
| `students/` | Student profiles and academic status |
| `courses/` | Courses, semesters, course sections, and schedules |
| `registration/` | Course registration and cancellation |
| `grades/` | Grades, final scores, GPA, and gradebooks |
| `search/` | Student search and filtering |
| `common/` | Shared permissions, pagination, contracts, and utilities |
| `templates/` | Django HTML templates |
| `static/` | CSS and JavaScript assets |
| `docs/` | Test plan and work breakdown |
| `config/` | Django settings and URL configuration |

## Prerequisites

- Python 3.12 or newer.
- MySQL 8.0 or Docker Desktop.
- Git.
- PowerShell on Windows.

## Environment Configuration

All commands below must be run from this directory.

```powershell
cd Implementation_and_testing

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure the variables in `.env`:

| Variable | Purpose | Example |
|---|---|---|
| `DB_NAME` | Database name | `student_mgmt` |
| `DB_USER` | Application database user | `sms_user` |
| `DB_PASSWORD` | Application database password | Replace with a secure password |
| `DB_ROOT_PASSWORD` | MySQL root password for Docker | Replace with a secure password |
| `DB_HOST` | Database host | `127.0.0.1` |
| `DB_PORT` | Database port | `3307` |
| `SECRET_KEY` | Django secret key | Replace with a random value |
| `DEBUG` | Django debug mode | `1` |

Do not commit `.env` or real credentials.

### Windows and mysqlclient

If installing `mysqlclient` fails on Windows, install and enable PyMySQL:

```powershell
python -m pip install pymysql
```

The Django settings already attempt to load PyMySQL before connecting to
MySQL.

## Run Locally

Make sure MySQL is running and the values in `.env` match your database.
Then run:

```powershell
python manage.py migrate
python manage.py seed
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

The seed command is repeatable and creates sample accounts, courses, semesters,
course sections, registrations, and grades.

## Run with Docker Compose

Docker Compose starts MySQL and the web application:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

- Web application: <http://127.0.0.1:8000/>
- MySQL host port: `3307`
- MySQL container port: `3306`
- Database data: Docker volume `db_data`

The web container waits for MySQL, applies migrations, and collects static
files before starting Gunicorn.

Create sample data manually if needed:

```powershell
docker compose exec web python manage.py seed --force
```

Reset existing sample passwords:

```powershell
docker compose exec web python manage.py seed --reset-passwords --force
```

Common container commands:

```powershell
docker compose ps
docker compose logs -f web
docker compose stop
docker compose down
```

Use `docker compose down -v` only when you also want to delete all MySQL data
stored in the Docker volume.

## Sample Accounts

The default seed password is `Pass1234`:

| Account | Role |
|---|---|
| `AD001` | Administrator |
| `GV001` | Teacher |
| `100001` | Student |

Create or refresh sample data locally:

```powershell
python manage.py seed
python manage.py seed --reset-passwords
```

Use `--password` to select a different seed password.

## Testing

Run the complete test suite:

```powershell
pytest
```

Run a specific test package or file:

```powershell
pytest accounts/tests
pytest grades/tests/test_calculator.py
pytest registration/tests/test_concurrency.py
pytest search/tests/test_views.py
```

Check Django migrations:

```powershell
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

Run Django system checks:

```powershell
python manage.py check
```

The testing plan and cross-review assignments are documented in:

- [Test Plan](docs/TEST_PLAN.md)
- [Work and Testing Breakdown](docs/WORK_BREAKDOWN.md)
- [Test Case Spreadsheet](Test_Cases_Student_Management.xlsx)

## Development Guidelines

- Read [DECISIONS.md](DECISIONS.md) and
  [common/contract.py](common/contract.py) before changing shared rules.
- Check permissions on the server; do not rely only on hiding interface controls.
- Use transactions and atomic updates when changing course-section capacity.
- Include migrations and tests for every model change.
- Do not commit `.env`, secrets, real personal data, or build artifacts.
- Follow the grade, prerequisite, status-transition, and gradebook-lock rules
  in `DECISIONS.md`.

## Project Documentation

- [Project Overview](../README.md)
- [System Requirements](../Requirement%20Specification%20and%20Design%20Document/Stage%201/System%20Requirement%20Specification%20Student%20Management%20System.pdf)
- [Design Decisions](DECISIONS.md)
- [Test Plan](docs/TEST_PLAN.md)
- [Work Breakdown](docs/WORK_BREAKDOWN.md)
