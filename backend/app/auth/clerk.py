import logging
from typing import Annotated

from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_frontend_origins, get_setting

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)

clerk_options = AuthenticateRequestOptions(
    jwt_key=get_setting("CLERK_JWT_KEY"),
    authorized_parties=get_frontend_origins(),
    accepts_token=["session_token"],
)


def require_clerk_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Clerk session token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_state = authenticate_request(request, clerk_options)
    if auth_state.reason is not None:
        logger.info("Clerk verification failed: %s", auth_state.reason.name)
    payload = auth_state.payload or {}
    clerk_user_id = payload.get("sub")

    if not auth_state.is_signed_in or not isinstance(clerk_user_id, str) or not clerk_user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid Clerk session token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return clerk_user_id
