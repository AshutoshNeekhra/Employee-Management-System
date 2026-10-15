from fastapi import APIRouter, HTTPException, status

from ..auth import authenticate, create_token
from ..schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse, summary="Obtain an access token")
def login(body: LoginRequest):
    if not authenticate(body.username, body.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    return TokenResponse(access_token=create_token(body.username))
