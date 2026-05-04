import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select, col
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "")
assert SECRET_KEY, "SECRET_KEY not set in environment"
ALGORITHM = "HS256"

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    email: str = Field(unique=True)
    password: str

class SaveStateCreate(BaseModel):
    game_title: str
    state: str
    score: int
    
class SaveState(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    game_title: str
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state: str
    score: int

app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL", "")
assert DATABASE_URL, "DATABASE_URL not set in environment"
engine = create_engine(DATABASE_URL)
ph = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

SQLModel.metadata.create_all(engine)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded["sub"]
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")
    with Session(engine) as session:
        db_user = session.get(User, user_id)
        if not db_user:
            raise HTTPException(404, "User doesn't exists")
        return db_user


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/users/", response_model=list[UserResponse])
def get_users():
    with Session(engine) as session:
        statement = select(User)
        results = session.exec(statement)
        db_users = results.all()
        return db_users

@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int):
    with Session(engine) as session:
        db_user = session.get(User, user_id)
        if not db_user:
            raise HTTPException(404, "User doesn't exists")
        return db_user

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate):
    try:
        hash = ph.hash(user.password)
        user_created = User(username=user.username, email=user.email, password=hash)
        with Session(engine) as session:
            session.add(user_created)
            session.commit()
            session.refresh(user_created)
        return user_created
    except IntegrityError:
        raise HTTPException(409, "Email already exists")
    
@app.post("/auth/login")
def login(user: UserLogin):
    with Session(engine) as session:
        statement = select(User).where(User.username == user.username)
        results = session.exec(statement).first()
        if not results:
            raise HTTPException(404, "User doesn't exists")
        try:
            ph.verify(results.password, user.password)
        except VerifyMismatchError:
            raise HTTPException(401, "Wrong password")
        return {"access_token": jwt.encode({"sub": str(results.id)}, SECRET_KEY, algorithm=ALGORITHM)}

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserCreate, current_user: User = Depends(get_current_user)):
    if user_id != current_user.id:
        raise HTTPException(403, "You can only update your own account")
    with Session(engine) as session:
        db_user = session.get(User, user_id)
        if not db_user:
            raise HTTPException(404, "User doesn't exists")
        db_user.username = user.username
        db_user.email = user.email
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        if user_id != current_user.id:
            raise HTTPException(403, "You can only delete your own account")
        db_user = session.get(User, user_id)
        if not db_user:
            raise HTTPException(404, "User doesn't exists")
        session.delete(db_user)
        session.commit()
        return {"message": f"User {db_user.username} deleted"}
    
@app.post("/saves/")
def create_save(save: SaveStateCreate, current_user: User = Depends(get_current_user)):
    assert current_user.id is not None
    save_created = SaveState(user_id=current_user.id, game_title=save.game_title, state=save.state, score=save.score)
    with Session(engine) as session:
        session.add(save_created)
        session.commit()
        session.refresh(save_created)
        return save_created
    
@app.get("/saves/{user_id}")
def get_save(user_id: int):
    with Session(engine) as session:
        db_user = session.get(User, user_id)
        if not db_user:
            raise HTTPException(404, "User doesn't exists")
        statement = select(SaveState).where(SaveState.user_id == user_id)
        results = session.exec(statement)
        db_saves = results.all()
        return db_saves
    
@app.get("/laderboards/{game_title}")
def get_laderboard(game_title: str):
    with Session(engine) as session:
        statement = select(SaveState).where(SaveState.game_title == game_title).order_by(col(SaveState.score).desc())
        results = session.exec(statement)
        db_lader = results.all()
        return db_lader