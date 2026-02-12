from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, hash_password
from app.models.user import User, UserRole
from app.schemas.auth import Token, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return Token(access_token=token)


@router.post("/setup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def initial_setup(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Create the first admin user. Only works if no users exist."""
    result = await db.execute(select(User).limit(1))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario. Use /login.",
        )
    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=UserRole.ADMIN,
    )
    db.add(user)
    await db.flush()
    token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return Token(access_token=token)
