# Page to Voice: Intelligent Audiobook Generation and Listening Platform

**Page to Voice** is a modern platform that converts documents and books into high-quality, narrated audiobooks with real-time listening progress tracking and intelligent text processing.

---

## Project Architecture

The project is organized as a decoupled monorepo:

```
page-to-voice/
├── backend/                  # FastAPI REST API & Database Layer
│   ├── .env.example          # Environment variables template
│   ├── .gitignore            # Backend gitignore rules
│   ├── database.py           # Database connection & session setup
│   ├── main.py               # Application entrypoint & route definitions
│   ├── models.py             # SQLAlchemy ORM entities & relationships
│   ├── requirements.txt      # Python dependencies
│   ├── schemas.py            # Pydantic request/response models
│   ├── security.py           # Password hashing & JWT authentication
│   ├── seed.py               # Database initialization & default admin seeder
│   └── README.md             # Backend-specific instructions
├── frontend/                 # Client user interface
└── README.md                 # Project documentation
```

---

## Tech Stack (Backend)

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (0.110.0)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/) (0.28.0)
- **Database:** [MySQL](https://www.mysql.com/) with [PyMySQL](https://pymysql.readthedocs.io/)
- **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/)
- **Authentication:** JWT ([PyJWT](https://pyjwt.readthedocs.io/)) with password hashing via [Passlib (bcrypt)](https://passlib.readthedocs.io/)
- **Configuration:** [python-dotenv](https://github.com/theskumar/python-dotenv)

---

## Database Models

The relational database layer features cascading foreign keys and indexes:

| Table | Description |
|---|---|
| `users` | Accounts with roles (`user`, `admin`), hashed passwords, and active status flags. |
| `documents` | Uploaded books or documents (`book`, `document`), source files, and language settings. |
| `chapters` | Extracted chapters containing raw text, processed text, audio URLs, and duration. |
| `listening_progress` | Per-user, per-document bookmarking with timestamps and completion status. |
| `processing_jobs` | Background job tracker (`pending`, `processing`, `completed`, `failed`) for conversions. |

---

## Getting Started (Backend)

### Prerequisites

- Python 3.10+
- MySQL Server 8.0+ running locally or remotely

### 1. Navigate to Backend

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

Create `.env` inside `backend/` (refer to `.env.example`):

```dotenv
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=page_to_voice_db
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **Note:** Ensure the database exists in MySQL (`CREATE DATABASE IF NOT EXISTS page_to_voice_db;`).

### 5. Initialize & Seed Database

Run the database seed script to automatically create all tables and insert the default administrator account:

```powershell
python seed.py
```

- **Default Admin Email:** `admin@pagetovoice.com`
- **Default Admin Password:** `admin123`

### 6. Start the API Server

```powershell
uvicorn main:app --reload --port 8000
```

The server will start at `http://127.0.0.1:8000`.

---

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/health` | Verifies server and database connection | No |
| `POST` | `/auth/register` | Registers a new user account | No |
| `POST` | `/auth/login` | Validates credentials and returns JWT token | No |
| `GET` | `/users/me` | Fetches details of the authenticated user | **Yes** (Bearer Token) |

### Interactive API Documentation

Once the server is running, visit:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## License

This project is licensed under the MIT License.
