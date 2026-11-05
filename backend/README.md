# Page to Voice - Backend API

Intelligent Audiobook Generation and Listening Platform API built with **FastAPI**, **SQLAlchemy 2.0**, **MySQL**, and hardened **JWT Authentication**.

---

## Tech Stack & Architecture

- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (0.110.0+)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/) (0.28.0+)
- **Database:** [MySQL](https://www.mysql.com/) 8.0+ via [PyMySQL](https://pymysql.readthedocs.io/)
- **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Data Validation & Serialization:** [Pydantic v2](https://docs.pydantic.dev/)
- **Authentication & Security:**
  - JWT tokens via `PyJWT` with claims validation (`iss`, `aud`, `iat`, `exp`, `jti`).
  - Bcrypt password hashing (`Passlib`) with 12 calculation rounds.
  - In-memory rate limiting against brute-force and credential stuffing attacks (5 attempts, 15-minute lockout).
  - Dummy hash computation to mitigate user enumeration timing attacks.
  - OWASP Security Headers middleware (`X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Referrer-Policy`).
  - Cross-Origin Resource Sharing (CORS) configured for frontend communication.

---

## Project Structure

```
backend/
├── database.py       # SQLAlchemy engine, session maker & get_db dependency
├── main.py           # FastAPI application, route handlers & middlewares
├── models.py         # SQLAlchemy database models & relationship mapping
├── requirements.txt  # Python package requirements
├── schemas.py        # Pydantic request/response validation schemas
├── security.py       # JWT creation/verification, password hashing & rate limiter
├── seed.py           # Database initialisation and default admin account seeder
├── .env              # Environment secrets (ignored by Git)
├── .env.example      # Template for environment configuration
└── README.md         # Backend documentation
```

---

## Setup & Running

### Prerequisites

- Python 3.10+
- MySQL Server 8.0+ running locally or remotely

### 1. Navigate to Backend Directory

```powershell
cd backend
```

### 2. Set Up Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env` in `backend/` (refer to `.env.example`):

```dotenv
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=page_to_voice_db
SECRET_KEY=super_secret_jwt_key_page_to_voice_2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **Note:** Create the MySQL database if it doesn't already exist:
> ```sql
> CREATE DATABASE IF NOT EXISTS page_to_voice_db;
> ```

### 5. Initialize & Seed Database

Run the database seed script to automatically create all tables and create/update the default administrator account:

```powershell
python seed.py
```

- **Default Admin Email:** `admin@pagetovoice.com`
- **Default Admin Username:** `admin`
- **Default Admin Password:** `1234@1234`

### 6. Start the API Server

```powershell
uvicorn main:app --reload --port 8000
```

The server starts at **`http://127.0.0.1:8000`**.

---

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/health` | Verifies server and database connection | No |
| `POST` | `/auth/register` | Registers a new user account | No |
| `POST` | `/auth/login` | Validates credentials and returns JWT access token | No |
| `GET` | `/users/me` | Fetches details of the authenticated user | **Yes** (Bearer Token) |

### 1. Health Check
- **`GET /health`**
- **Response `200 OK`:**
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "service": "Page to Voice API"
  }
  ```

### 2. User Registration
- **`POST /auth/register`**
- **Payload:**
  ```json
  {
    "username": "alex_reader",
    "email": "alex@example.com",
    "password": "Password123!"
  }
  ```
  *Validation Rules:*
  - `username`: 3–50 characters, letters, numbers, underscores, and hyphens only.
  - `password`: minimum 8 characters, at least 1 digit, 1 letter, and 1 special character, no spaces.
- **Response `201 Created`:**
  ```json
  {
    "id": 2,
    "email": "alex@example.com",
    "username": "alex_reader",
    "role": "user",
    "is_active": true,
    "created_at": "2026-11-05T09:57:00"
  }
  ```

### 3. User Login
- **`POST /auth/login`**
- **Payload:** Accepts either `email` or `username`:
  ```json
  {
    "email": "admin@pagetovoice.com",
    "password": "1234@1234"
  }
  ```
  *or*
  ```json
  {
    "username": "admin",
    "password": "1234@1234"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
  }
  ```

### 4. Authenticated Profile
- **`GET /users/me`**
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
  ```json
  {
    "id": 1,
    "email": "admin@pagetovoice.com",
    "username": "admin",
    "role": "admin",
    "is_active": true,
    "created_at": "2026-11-05T00:55:26"
  }
  ```

---

## Interactive API Documentation

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
