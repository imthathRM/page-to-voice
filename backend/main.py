from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import engine, Base, get_db
import models
import schemas
from security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to ensure DB tables are created on startup."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Database initialization error on startup: {e}")
    yield


app = FastAPI(
    title="Page to Voice API",
    description="Intelligent Audiobook Generation and Listening Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    """Register a new user, hash the password, and store in the database."""
    # Check if email is already registered
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # Create new user instance
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
    return db_user


@app.post(
    "/auth/login",
    response_model=schemas.Token,
    tags=["Authentication"],
)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Authenticate user credentials and return a signed JWT access token."""
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value if hasattr(user.role, "value") else str(user.role)}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get(
    "/users/me",
    response_model=schemas.UserResponse,
    tags=["Users"],
)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    """Protected route returning details of the currently authenticated user."""
    return current_user
