# Page to Voice - Frontend Client

A responsive React single-page application for the **Page to Voice** platform, built with **React 19**, **Vite**, and pure vanilla CSS with responsive design.

---

## Features

- **Authentication Flows:**
  - Dual-identifier Login (supports either username or email address).
  - User Registration with real-time password complexity validation.
  - Interactive Account Profile with session management and secure Sign Out modal.
- **Backend Integration:**
  - Centralized API client (`apiClient.js`) with native `fetch`, bearer token injection, and structured FastAPI error parsing.
  - Persistent authentication via `localStorage` with automatic session restoration on page reload.
  - Development proxy in `vite.config.js` forwarding requests to the FastAPI backend (`http://localhost:8000`).
- **Accessible & Modular Component Library:**
  - Reusable inputs (`TextInput`, `PasswordInput` with visibility toggle), buttons, alerts, modals, and spinners.
  - Zero external CSS frameworks—clean, modern CSS design tokens and variables.
- **Fast Tooling:**
  - Sub-second build times via Vite.
  - Code hygiene and linting with Oxlint.

---

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   ├── apiClient.js          # Centralized HTTP client, token storage & error handler
│   │   ├── authContracts.js      # Endpoint constants, adapters & data normalization
│   │   └── authService.js        # High-level auth actions (login, register, profile, health)
│   ├── components/
│   │   ├── common/               # UI design system components
│   │   │   ├── Alert/            # Feedback banner (success, error, warning, info)
│   │   │   ├── Button/           # Action buttons with variants and loading state
│   │   │   ├── Input/            # Accessible TextInput & PasswordInput
│   │   │   ├── LoadingSpinner/   # Visual loading indicator
│   │   │   └── Modal/            # Accessible modal dialog
│   │   ├── layout/
│   │   │   └── Navbar.jsx        # Top navigation header & user session pill
│   │   └── screens/
│   │       ├── LoginScreen.jsx   # Sign-in form (username/email + password)
│   │       ├── RegisterScreen.jsx# Account creation with validation rules
│   │       ├── AccountScreen.jsx # Authenticated user profile & system status
│   │       └── Screens.css       # Screen-level responsive layouts
│   ├── context/
│   │   ├── AuthContext.js        # React Context definition
│   │   ├── AuthProvider.jsx      # Session provider & automatic token rehydration
│   │   └── useAuth.js            # Consumer hook for authentication state
│   ├── App.jsx                   # Main layout and screen router
│   ├── main.jsx                  # Application entry point
│   ├── App.css                   # Global layout styling
│   └── index.css                 # Base resets and typography
├── .env                          # Local environment variables
├── .env.example                  # Environment template
├── vite.config.js                # Vite build config & dev proxy
└── package.json                  # Dependencies and scripts
```

---

## Getting Started

### Prerequisites

- **Node.js:** v18.0.0 or higher
- **npm:** v9.0.0 or higher
- **Backend Service:** Ensure the backend FastAPI server is running on `http://localhost:8000`.

### 1. Navigate to Frontend Directory

```powershell
cd frontend
```

### 2. Install Dependencies

```powershell
npm install
```

### 3. Configure Environment Variables

Create `.env` in `frontend/` (refer to `.env.example`):

```dotenv
# Backend API Base URL
VITE_API_BASE_URL=http://localhost:8000

# Set to 'true' only to simulate authentication when the backend is offline
VITE_ENABLE_AUTH_PREVIEW=false
```

### 4. Start Development Server

```powershell
npm run dev
```

The application will be accessible at: **`http://localhost:5173`**

---

## Available Scripts

| Command | Description |
|---|---|
| `npm run dev` | Starts the Vite development server with HMR at `http://localhost:5173` |
| `npm run build` | Compiles and bundles production-ready assets to `dist/` |
| `npm run preview` | Locally serves the production build from `dist/` |
| `npm run lint` | Runs `oxlint` to check code hygiene across the repository |

---

## Default Test Credentials

Use these seeded credentials after running the backend `seed.py`:

- **Username / Email:** `admin` or `admin@pagetovoice.com`
- **Password:** `1234@1234`
- **Role:** Administrator
