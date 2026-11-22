# Student Management System

This course project implements a student management system following the
complete software development process: analysis, design, implementation, and
testing. The project uses a client-server architecture with Django,
MySQL, and server-rendered web pages.

The system supports three roles:

- **Administrator:** manages accounts, students, courses, semesters, course sections, and grades.
- **Teacher:** views assigned student lists and manages and locks gradebooks.
- **Student:** views personal information, registers or cancels course sections, and views academic results.

## 1. Project Requirements

The project is completed by a group and covers analysis, design,
implementation, testing, and project management across the following four
stages.

### Stage 1 - Analysis and Requirements Specification

- Describe functional and non-functional requirements in natural language.
- Create a Use Case Diagram.
- Create a Data Flow Diagram (DFD).
- Create a Class Diagram.

Main documents:

- [System Requirement Specification](Requirement%20Specification%20and%20Design%20Document/Stage%201/System%20Requirement%20Specification%20Student%20Management%20System.pdf)
- [Use Case Diagram](Requirement%20Specification%20and%20Design%20Document/Stage%201/Use_case_diagram/Use_case_diagram.drawio.pdf)
- [Data Flow Diagram](Requirement%20Specification%20and%20Design%20Document/Stage%201/DFD_diagram/DFD_diagram.drawio.pdf)
- [Class Diagram](Requirement%20Specification%20and%20Design%20Document/Stage%201/Class_diagram/Class_diagram.drawio.pdf)

### Stage 2 - Design

- Design graphical interfaces for administrators, teachers, and students.
- Design the client-server architecture.
- Design the database, tables, primary keys, foreign keys, and relationships.

Design documents:

- [Main GUI Design](Requirement%20Specification%20and%20Design%20Document/Stage%201/GUI/Student%20Management%20System%20GUI.pdf)
- [Additional GUI Design](Requirement%20Specification%20and%20Design%20Document/Stage%201/GUI/Student%20Management%20part%202.fig)
- [Client-Server Architecture](Requirement%20Specification%20and%20Design%20Document/Stage%201/Client-server/Client-server.drawio.pdf)
- [Database Model](Requirement%20Specification%20and%20Design%20Document/Stage%201/Data%20Model/Database%20model.drawio.pdf)

The agreed design decisions and conventions are documented in
[DECISIONS.md](Implementation_and_testing/DECISIONS.md).

### Stage 3 - Implementation

- Use Python 3.12 and Django 5.x.
- Use MySQL 8.0 as the database.
- Organize the source code as Django applications with a client-server
  architecture.
- Use Git for source control.
- Support deployment with Docker Compose, Gunicorn, and WhiteNoise.

The source code and deployment instructions are located in
[Implementation_and_testing](Implementation_and_testing).

### Stage 4 - Testing

- Create test cases for use cases and application features.
- Perform unit tests, integration tests, and concurrency tests.
- Test authentication, authorization, registration, scheduling conflicts,
  grade calculation, and GPA calculation.
- Record actual results, Pass/Fail outcomes, defects, and tester assignments.

Testing documents:

- [Test Plan](Implementation_and_testing/docs/TEST_PLAN.md)
- [Work and Testing Breakdown](Implementation_and_testing/docs/WORK_BREAKDOWN.md)
- [Test Cases](Implementation_and_testing/Test_Cases_Student_Management.xlsx)

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python 3.12 |
| Framework | Django 5.x |
| Database | MySQL 8.0 |
| Architecture | Client-server, server-rendered |
| Interface | Django Templates, HTML, CSS, JavaScript |
| Testing | pytest, pytest-django |
| Deployment | Docker Compose, Gunicorn, WhiteNoise |

## Main Features

- Login, logout, account locking, and role-based authorization.
- Manage accounts, student profiles, teacher profiles, courses, semesters,
  and course sections.
- Search, filter, and paginate application data.
- Validate capacity, scheduling conflicts, semester registration periods,
  and course prerequisites.
- Register for and cancel course sections safely through transactions.
- Enter grades, calculate final scores, convert grades to letters and GPA,
  and lock or unlock gradebooks.
- Generate sample data and database migrations for MySQL.

## Repository Structure

```text
Student-Management-System/
|-- Implementation_and_testing/          # Source code, migrations, and tests
|   |-- accounts/                        # Accounts, roles, and seed data
|   |-- students/                        # Student profiles and academic status
|   |-- courses/                         # Courses, semesters, and sections
|   |-- registration/                    # Registration and cancellation
|   |-- grades/                          # Grades and GPA
|   |-- search/                          # Search and filtering
|   |-- common/                          # Permissions, pagination, and contracts
|   |-- templates/                       # Django templates
|   |-- static/                          # CSS and JavaScript
|   |-- docs/                            # Test plans and work breakdown
|   |-- config/                          # Django configuration
|   |-- docker-compose.yml
|   |-- dockerfile
|   `-- requirements.txt
|-- Requirement Specification and Design Document/
|   `-- Stage 1/                         # SRS, DFD, use cases, class and GUI
|-- Work Assignment/
|   `-- Work assignment.docx             # Team work assignment
`-- README.md                            # Overall project overview
```

The `Student-Management-System-main/` directory contains an archived copy or
additional project resources. The primary source code is developed in
`Implementation_and_testing/`.

## System Requirements

- Windows 10/11 or a compatible environment.
- Python 3.12 or newer.
- MySQL 8.0 or Docker Desktop.
- PowerShell and Git.

## Local Setup and Execution

Run the following commands in `Implementation_and_testing`:

```powershell
cd Implementation_and_testing

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Update `DB_PASSWORD`, `DB_ROOT_PASSWORD`, `SECRET_KEY`, and the database
variables in `.env`. Default values are documented in the
[implementation README](Implementation_and_testing/README.md).

Once MySQL is ready:

```powershell
python manage.py migrate
python manage.py seed
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

Do not commit `.env`, real passwords, or real personal data.

## Run with Docker Compose

Run in `Implementation_and_testing`:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The application is available at <http://127.0.0.1:8000/>. MySQL is mapped to
host port `3307` and its data is stored in the `db_data` Docker volume.

Common commands:

```powershell
docker compose ps
docker compose logs -f web
docker compose exec web python manage.py seed --force
docker compose stop
docker compose down
```

`docker compose down -v` permanently deletes all MySQL data in the volume.

## Sample Accounts

Running `python manage.py seed` creates repeatable sample data. The default
password is `Pass1234`:

| Account | Role |
|---|---|
| `AD001` | Administrator |
| `GV001` | Teacher |
| `100001` | Student |

Reset passwords for existing sample accounts:

```powershell
python manage.py seed --reset-passwords
```

## Testing

Run the complete test suite:

```powershell
pytest
```

Run a specific test scope:

```powershell
pytest accounts/tests
pytest grades/tests/test_calculator.py
pytest registration/tests/test_concurrency.py
```

Check migrations after changing models:

```powershell
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

## Development Guidelines

- Read [DECISIONS.md](Implementation_and_testing/DECISIONS.md) and
  [common/contract.py](Implementation_and_testing/common/contract.py) before
  changing shared rules.
- Enforce permissions on the server rather than only hiding interface controls.
- Use transactions and atomic updates when changing registration capacity.
- Include migrations and tests for every model change.
- Do not commit configuration files, secrets, or real personal data.

## References

- [Implementation README](Implementation_and_testing/README.md)
- [SRS and Stage 1 Design](Requirement%20Specification%20and%20Design%20Document/Stage%201/)
- [Work Assignment](Work%20Assignment/Work%20assignment.docx)
- [Design Decisions](Implementation_and_testing/DECISIONS.md)
- [Test Plan](Implementation_and_testing/docs/TEST_PLAN.md)
- [Work Breakdown](Implementation_and_testing/docs/WORK_BREAKDOWN.md)
- [Test Cases](Implementation_and_testing/Test_Cases_Student_Management.xlsx)
