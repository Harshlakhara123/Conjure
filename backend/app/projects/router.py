from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from typing import Annotated
from app.auth.access import require_application_user, require_owned_project
from app.auth.clerk import require_clerk_user
from app.db_session import get_db_session
from app.projects.repository import ProjectRepository
from app.projects.schemas import ProjectCreate, ProjectResponse , ProjectRename


router = APIRouter(prefix='/projects',tags=['projects'])

@router.post('',response_model=ProjectResponse, status_code=201)
async def create_project(
    request: ProjectCreate,
    clerk_user_id: Annotated[str, Depends(require_clerk_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProjectResponse:
    async with session.begin():

        user = await require_application_user(session, clerk_user_id)

        project = await ProjectRepository(session).create_project(
            name=request.name,
            owner_id=user.id
        )

    return ProjectResponse.model_validate(project)

@router.get('',response_model=list[ProjectResponse])
async def list_projects_by_owner(
    clerk_user_id: Annotated[str,Depends(require_clerk_user)],
    session: Annotated[AsyncSession,Depends(get_db_session)],
) -> list[ProjectResponse]:
    async with session.begin():
        user = await require_application_user(session, clerk_user_id)

        projects = await ProjectRepository(session).list_by_owner(owner_id=user.id)
    return [ProjectResponse.model_validate(project) for project in projects]

@router.get("/{project_id}",response_model=ProjectResponse)
async def get_project_by_id(
    project_id: UUID,
    clerk_user_id: Annotated[str,Depends(require_clerk_user)],
    session: Annotated[AsyncSession,Depends(get_db_session)],
) -> ProjectResponse:
    async with session.begin():
        project = await require_owned_project(session, clerk_user_id, project_id)

    return ProjectResponse.model_validate(project)

@router.patch('/{project_id}',response_model=ProjectResponse)
async def update_project_name(
    request: ProjectRename,
    project_id: UUID,
    clerk_user_id: Annotated[str, Depends(require_clerk_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProjectResponse:
    async with session.begin():
        project = await require_owned_project(session, clerk_user_id, project_id)
        project = await ProjectRepository(session).rename_for_owner(
            project_id=project_id,
            owner_id=project.owner_id,
            new_name=request.name,
        )
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse.model_validate(project)
