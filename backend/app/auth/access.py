from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.model import Project
from app.projects.repository import ProjectRepository
from app.users.model import User
from app.users.repository import UserRepository


async def require_application_user(session: AsyncSession, clerk_user_id: str) -> User:
    user = await UserRepository(session).get_by_clerk_id(clerk_user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Application user not found")
    return user


async def require_owned_project(
    session: AsyncSession,
    clerk_user_id: str,
    project_id: UUID,
    *,
    for_update: bool = False,
    not_found_detail: str = "Project not found",
) -> Project:
    project = await ProjectRepository(session).get_by_id_for_clerk_user(
        project_id, clerk_user_id, for_update=for_update
    )
    if project is None:
        raise HTTPException(status_code=404, detail=not_found_detail)
    return project
