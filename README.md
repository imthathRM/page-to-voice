# Page to Voice: Intelligent Audiobook Generation and Listening Platform

**Page to Voice** is a modern platform that converts documents and books into high-quality, narrated audiobooks with real-time listening progress tracking, intelligent text processing, and a hardened authentication system.

---

## Project Architecture

The project is structured as a decoupled full-stack monorepo:

```
page-to-voice/
├── backend/                  # FastAPI REST API & Database Layer
│   ├── .env.example          # Backend environment template
│   ├── database.py           # Database connection & session setup
│   ├── main.py               # Application entrypoint, CORS & route definitions
│   ├── models.py             # SQLAlchemy ORM entities & relationships
│   ├── requirements.txt      # Python dependencies
│   ├── schemas.py            # Pydantic request/response models
│   ├── security.py           # Password hashing, JWT & rate limiter
│   ├── seed.py               # Database initialization & default admin seeder
│   └── README.md             # Backend-specific instructions
│
├── frontend/                 # React 19 Client User Interface
│   ├── .env.example          # Frontend environment template
│   ├── vite.config.js        # Vite build configuration & API reverse proxy
│   ├── src/
│   │   ├── api/              # Centralized API client & authentication service
│   │   ├── components/       # Design system (screens, layouts, UI components)
│   │   ├── context/          # React AuthContext & session provider
│   │   ├── App.jsx           # Application shell & screen router
│   │   └── main.jsx          # React DOM root entrypoint
│   └── README.md             # Frontend-specific instructions
│
└── README.md                 # Root documentation
```

---

## Tech Stack

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (0.110.0+)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/) (0.28.0+)
- **Database:** [MySQL](https://www.mysql.com/) 8.0+ with [PyMySQL](https://pymysql.readthedocs.io/)
- **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/)
- **Authentication:** JWT ([PyJWT](https://pyjwt.readthedocs.io/)) with password hashing via [Passlib (bcrypt)](https://passlib.readthedocs.io/) (12 rounds)
- **Security Features:** Brute-force rate limiting, constant-time verification against timing attacks, OWASP security headers, dual identifier login (username or email), and password complexity policies.

### Frontend
- **Framework:** [React 19](https://react.dev/)
- **Build Tool:** [Vite](https://vite.dev/)
- **Code Linter:** [Oxlint](https://oxc.rs/)
- **Styling:** Modular vanilla CSS with responsive design and theme variables
- **State Management:** React Context API with persistent token storage (`localStorage`)

---

## Quick Start (Running Backend & Frontend)

### 1. Start the Backend API

1. Navigate to `backend`:
   ```powershell
   cd backend
   ```
2. Set up virtual environment and install dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Configure environment variables in `backend/.env` (refer to `.env.example`).
4. Initialize the database and create tables:
   ```powershell
   python seed.py
   ```
5. Start the API server:
   ```powershell
   uvicorn main:app --reload --port 8000
   ```
   *The backend will be running at `http://127.0.0.1:8000`.*

### 2. Start the Frontend Client

In a separate terminal:

1. Navigate to `frontend`:
   ```powershell
   cd frontend
   ```
2. Install dependencies:
   ```powershell
   npm install
   ```
3. Configure environment variables in `frontend/.env`:
   ```dotenv
   VITE_API_BASE_URL=http://localhost:8000
   VITE_ENABLE_AUTH_PREVIEW=false
   ```
4. Start the frontend development server:
   ```powershell
   npm run dev
   ```
   *The frontend will be running at `http://localhost:5173`.*

---

## Default Administrator Credentials

Once `python seed.py` has run:

| Field | Value |
|---|---|
| **Email** | `admin@pagetovoice.com` |
| **Username** | `admin` |
| **Password** | `1234@1234` |
| **Role** | `admin` |

---

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/health` | Verifies server and database connection | No |
| `POST` | `/auth/register` | Registers a new user account | No |
| `POST` | `/auth/login` | Validates credentials and returns JWT access token | No |
| `GET` | `/users/me` | Fetches details of the authenticated user | **Yes** (Bearer Token) |

### Interactive API Documentation
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

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

## License

This project is licensed under the MIT License.
