from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_frontend_origins
from app.db_session import engine, get_db_session
from app.auth.router import router as auth_router
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(title="Conjure API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_frontend_origins(),
    allow_methods=["GET","POST"],
    allow_headers=["Authorization"],
)
app.include_router(auth_router)
app.include_router(users_router)

@app.get("/health/db")
async def database_health(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"database": "connected"}

