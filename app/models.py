# app/models.py
from pydantic import BaseModel, Field
from typing import Optional

# Models for authentication
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str

class RegisterRequest(BaseModel):
    username: str
    password: str

class RegisterResponse(BaseModel):
    message: str

# Models for CSV operations
# We use aliases so that our field names match the CSV headers exactly.
class CSVRecord(BaseModel):
    user: str
    broker: str
    api_key: str = Field(..., alias="API key")
    api_secret: str = Field(..., alias="API secret")
    pnl: float
    margin: float
    max_risk: float

    class Config:
        allow_population_by_field_name = True

# For updating a record, identify it by its "user" field.
class CSVRecordUpdate(BaseModel):
    user: str  # record identifier
    broker: Optional[str] = None
    api_key: Optional[str] = Field(None, alias="API key")
    api_secret: Optional[str] = Field(None, alias="API secret")
    pnl: Optional[float] = None
    margin: Optional[float] = None
    max_risk: Optional[float] = None

    class Config:
        allow_population_by_field_name = True
