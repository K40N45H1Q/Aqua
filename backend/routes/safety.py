from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlmodel import Session, select
from hashlib import sha256
from database.models import User, engine
from datetime import datetime, timedelta
import jwt, os, secrets

SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter()


@router.post("/create_account")
async def create_account(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing fields")
    with Session(engine) as session:
        if session.exec(select(User).where(User.username == username)).first():
            raise HTTPException(status_code=400, detail="User already exists")  # ← вот это было убрано
        user = User(
            username=username,
            account_type=data.get("account_type"),
            hashed_password=sha256(password.encode()).hexdigest()
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"status": "ok", "user_id": user.id}


@router.post("/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing fields")
    hashed = sha256(password.encode()).hexdigest()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user or user.hashed_password != hashed:
            raise HTTPException(status_code=400, detail="Invalid email or password")
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token = jwt.encode({"user_id": user.id, "exp": expire.timestamp()}, SECRET_KEY, algorithm=ALGORITHM)
        return {"status": "ok", "token": token}


def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user


@router.get("/get_me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "account_type": current_user.account_type}