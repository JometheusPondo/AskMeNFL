from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from models.user import User
from database.userDB import UserDatabase
from utils.jwt import verifyToken

security = HTTPBearer()

def getCurrentUser(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: UserDatabase = None
) -> User:
    pass


def getOptionalUser(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: UserDatabase = None
) -> Optional[User]:
    pass