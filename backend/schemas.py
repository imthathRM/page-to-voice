import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        trimmed = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]+$", trimmed):
            raise ValueError("Username can only contain alphanumeric characters, underscores, and hyphens.")
        return trimmed


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("Password must contain at least one special character.")
        if " " in v:
            raise ValueError("Password must not contain spaces.")
        return v


class UserLogin(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_identifier(self):
        if not self.email and not self.username:
            raise ValueError("Either email or username must be provided to log in.")
        return self


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
