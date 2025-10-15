import os
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

def createAccessToken(data: dict, expiresMinutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    pass
