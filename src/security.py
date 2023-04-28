from datetime import timedelta, datetime
from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.crud import get_user
from src.database import get_db
# from src.main import oauth2_scheme
from src.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# TODO create env
SECRET_KEY = 'secret'
ALGORITHM = "HS256"


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(email: str, password: str, db_session) -> Union[bool, User]:
    db_user = get_user(email, db_session)
    if not db_user:
        return False
    if not verify_password(password, db_user.password):
        return False
    return db_user


ACCESS_TOKEN_EXPIRE_MINUTES = 10


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_access_token_from_email(email: str):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email}, expires_delta=access_token_expires
    )
    return access_token


def get_current_user(token=Depends(oauth2_scheme), db_session: Session = Depends(get_db)):
    print(token)
    try:
        decoded = jwt.decode(token, SECRET_KEY, ALGORITHM)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid or expired token')

    db_user = db_session.query(User).filter(User.email == decoded['sub']).first()
    if db_user:
        return db_user
    return False
