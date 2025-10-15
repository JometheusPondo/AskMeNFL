from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from models.user import User
from database.userDB import UserDatabase
from utils.jwt import verifyToken

_userDb: Optional[UserDatabase] = None
security = HTTPBearer()

def setUserDatabase(db: UserDatabase):
    global _userDb
    _userDb = db

def getUserDatabase() -> UserDatabase:
    if _userDb is None:
        raise HTTPException(
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
            detail = "Database not initialized"
        )

    return _userDb

def getCurrentUser(credentials: HTTPAuthorizationCredentials = Depends(security), db: UserDatabase = Depends(getUserDatabase)) -> User:
    token = credentials.credentials
    username = verifyToken(token)

    if username is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Unable to find username",
            headers = {"WWW-Authenticate": "Bearer"}
        )

    user = db.getUserByUsername(username)

    if user is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "User not found",
            headers = {"WWW-Authenticate": "Bearer"}
        )

    return user


def getOptionalUser(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error = False)), db: UserDatabase = Depends(getUserDatabase)) -> Optional[User]:
    if credentials is None:
        return None

    token = credentials.credentials
    username = verifyToken(token)

    if username is None:
        return None

    user = db.getUserByUsername(username)

    return user