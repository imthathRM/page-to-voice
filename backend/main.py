from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import engine, Base, get_db
import models
import schemas
from security import (
    get_password_hash,
    verify_password,
    verify_dummy_password,
    create_access_token,
    get_current_user,
    login_rate_limiter,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to ensure DB tables are created on startup."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"Database initialization warning on startup: {e}")
    yield


app = FastAPI(
    title="Page to Voice API",
    description="Intelligent Audiobook Generation and Listening Platform API with Hardened Security",
    version="1.1.0",
    lifespan=lifespan,
)

# OWASP Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, taking proxy headers into account."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint that verifies database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "service": "Page to Voice API",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(exc)}",
        )


@app.post(
    "/auth/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user with strong password validation."""
    # Check if email is already registered
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # Check if username is already taken
    if db.query(models.User).filter(models.User.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken",
        )

    # Create new user with bcrypt hash (cost 12)
    hashed_password = get_password_hash(user_in.password)
    db_user = models.User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_password,
        role=models.UserRole.USER,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"New user registered: id={db_user.id}, email={db_user.email}")
    return db_user


@app.post(
    "/auth/login",
    response_model=schemas.Token,
    tags=["Authentication"],
)
def login(
    credentials: schemas.UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Hardened authentication endpoint:
    - Brute-force & rate-limiting protection per identifier and IP
    - Constant-time verification to prevent user enumeration (timing attacks)
    - Support for login by username OR email
    - Comprehensive security audit logging
    """
    client_ip = get_client_ip(request)
    identifier = (credentials.email or credentials.username or "").strip().lower()
    ip_key = f"ip:{client_ip}"
    user_key = f"user:{identifier}"

    # 1. Check Rate Limiting / Lockout Status
    is_ip_locked, ip_rem = login_rate_limiter.is_locked(ip_key)
    if is_ip_locked:
        logger.warning(f"Blocked login attempt from locked IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts from your IP. Temporarily locked for {max(1, ip_rem // 60)} minute(s).",
            headers={"Retry-After": str(ip_rem)},
        )

    is_user_locked, user_rem = login_rate_limiter.is_locked(user_key)
    if is_user_locked:
        logger.warning(f"Blocked login attempt for locked account: {identifier} from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to multiple failed login attempts. Try again in {max(1, user_rem // 60)} minute(s).",
            headers={"Retry-After": str(user_rem)},
        )

    # 2. Query user by email OR username
    user = (
        db.query(models.User)
        .filter(
            (models.User.email == identifier)
            | (models.User.username == identifier)
        )
        .first()
    )

    # 3. Constant-time verification & validation
    if not user:
        # Mitigate timing attack by hashing dummy password
        verify_dummy_password(credentials.password)
        login_rate_limiter.record_failure(ip_key)
        login_rate_limiter.record_failure(user_key)
        logger.warning(f"Failed login (user not found) for identifier: {identifier} from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(credentials.password, user.password_hash):
        login_rate_limiter.record_failure(ip_key)
        login_rate_limiter.record_failure(user_key)
        logger.warning(f"Failed login (invalid password) for user_id={user.id} from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Check account status
    if not user.is_active:
        logger.warning(f"Login attempted on inactive account user_id={user.id} from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended",
        )

    # 5. Successful login: reset failure counters
    login_rate_limiter.record_success(ip_key)
    login_rate_limiter.record_success(user_key)
    logger.info(f"Successful login for user_id={user.id} ({user.email}) from IP: {client_ip}")

    # 6. Issue hardened JWT token
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token, expires_in = create_access_token(
        data={"sub": user.email, "username": user.username, "role": role_val}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@app.get(
    "/users/me",
    response_model=schemas.UserResponse,
    tags=["Users"],
)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    """Protected route returning details of the currently authenticated user."""
    return current_user
