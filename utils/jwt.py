import os
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


# Takes in a dictionary containing items to encode in the token
# and the expiry time, set to 24 hours by default
# It returns an encoded JWT token string

def createAccessToken(data: dict, expiresMinutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    toEncode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes = expiresMinutes)
    toEncode["exp"] = expire

    encodedJwt = jwt.encode(toEncode, SECRET_KEY, algorithm = ALGORITHM)
    return encodedJwt


def verifyToken(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        username = payload.get("sub")

        if username is None:
            return None

        return username

    except JWTError:
        return None