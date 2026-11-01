from datetime import datetime, timedelta
from jose import jwt
from database import KULLANICILAR_DB

SECRET_KEY = "yalan_makinesi_gizli_anahtar_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def authenticate_user(username, password):
    user = KULLANICILAR_DB.get(username)
    if not user or user["password"] != password:
        return False
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)