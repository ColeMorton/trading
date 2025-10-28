"""
Authentication endpoints for session-based authentication.

This router provides login, logout, and user info endpoints for the SSE proxy
authentication system.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import validate_api_key
from ..models.schemas import LoginRequest, LoginResponse, LogoutResponse, UserInfo
from typing import Annotated


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Authenticate user and create session.

    Validates the provided API key and stores it in a secure session cookie.
    The session cookie is then used for subsequent SSE proxy requests.

    Args:
        credentials: Login credentials containing API key
        request: FastAPI request object
        db: Database session

    Returns:
        LoginResponse with user information

    Raises:
        HTTPException: If API key is invalid or inactive

    Example:
        ```javascript
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: 'your-api-key' })
        });
        const data = await response.json();
        console.log('Logged in as:', data.user.name);
        ```
    """
    # Validate API key using existing validation logic
    try:
        api_key_obj = await validate_api_key(credentials.api_key)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or authentication failed",
        ) from e

    # Store API key in session
    request.session["api_key"] = credentials.api_key
    request.session["api_key_id"] = api_key_obj.id
    request.session["user_name"] = api_key_obj.name

    # Create user info response
    user_info = UserInfo(
        id=api_key_obj.id,
        name=api_key_obj.name,
        scopes=api_key_obj.scopes,
        rate_limit=api_key_obj.rate_limit,
        is_active=api_key_obj.is_active,
    )

    return LoginResponse(user=user_info)


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request):
    """
    Clear session and logout user.

    Removes the session cookie and clears all stored session data.

    Args:
        request: FastAPI request object

    Returns:
        LogoutResponse confirming logout

    Example:
        ```javascript
        await fetch('/api/v1/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        ```
    """
    # Clear session data
    request.session.clear()

    return LogoutResponse()


@router.get("/me", response_model=UserInfo)
async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get current authenticated user information from session.

    Retrieves user information for the currently authenticated session.
    Requires an active session (user must be logged in).

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        UserInfo with current user details

    Raises:
        HTTPException: If user is not authenticated

    Example:
        ```javascript
        const response = await fetch('/api/v1/auth/me', {
            credentials: 'include'
        });
        const user = await response.json();
        console.log('Current user:', user.name);
        ```
    """
    # Check if user is authenticated
    if "api_key" not in request.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login first.",
        )

    # Retrieve API key from session and validate it's still active
    api_key = request.session["api_key"]

    try:
        api_key_obj = await validate_api_key(api_key)
    except HTTPException as e:
        # API key is no longer valid, clear session
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or API key no longer valid. Please login again.",
        ) from e

    # Return user info
    return UserInfo(
        id=api_key_obj.id,
        name=api_key_obj.name,
        scopes=api_key_obj.scopes,
        rate_limit=api_key_obj.rate_limit,
        is_active=api_key_obj.is_active,
    )
