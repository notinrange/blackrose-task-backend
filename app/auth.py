# app/auth.py
from fastapi import APIRouter, HTTPException, Depends
from app.models import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.database import get_db
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()

SECRET_KEY = "your_secret_key"  # Replace with a secure key in production
ALGORITHM = "HS256"
security = HTTPBearer()

def create_token(username: str) -> str:
    token = jwt.encode({"username": username}, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("username")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token or user")
    return username

@router.post("/register", response_model=RegisterResponse)
def register(register_request: RegisterRequest):
    username = register_request.username
    password = register_request.password
    conn = get_db()
    cursor = conn.cursor()
    # Check if the user already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    # Insert the new user
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()
    return RegisterResponse(message="User registered successfully")

@router.post("/login", response_model=LoginResponse)
def login(login_request: LoginRequest):
    username = login_request.username
    password = login_request.password
    conn = get_db()
    cursor = conn.cursor()
    # Verify credentials against the users table
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(username)
    # Optionally store the session token
    cursor.execute("INSERT INTO sessions (username, token) VALUES (?, ?)", (username, token))
    conn.commit()
    conn.close()
    return LoginResponse(token=token)
