from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from server.constants import API_KEY


def authentication(api_key: str = Depends(OAuth2PasswordBearer(tokenUrl='token'))):
    if api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
