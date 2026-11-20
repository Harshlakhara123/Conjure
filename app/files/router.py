from fastapi import APIRouter , Depends , HTTPException
from uuid import UUID
from typing import Annotated
from app.auth.clerk import require_clerk_user
from app.db_session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.repository import UserRepository
from app.projects.repository import ProjectRepository
from app.files.repository import FileRepository

from app.files.schemas import FileEntryResponse,FileEntryCreate
router = APIRouter(prefix='/projects/{project_id}/files')

@router.post("",response_model=FileEntryResponse,status_code=201)
async def create_file(
    request:FileEntryCreate,
    project_id:UUID,
    clerk_user_id: Annotated[str, Depends(require_clerk_user)],
    session:Annotated[AsyncSession, Depends(get_db_session)],
) -> FileEntryResponse:
    async with session.begin():

        user = await UserRepository(session).get_by_clerk_id(clerk_user_id)
        if user is None:
            raise HTTPException(status_code=404,detail="application user not found")

        project = await ProjectRepository(session).get_by_id_for_owner(
            project_id=project_id,
            owner_id=user.id
        )
        if project is None:
            raise HTTPException(status_code=404,detail="Project not found")

        file_repository = FileRepository(session)
        if request.parent_id is not None:
            parent = await file_repository.get_by_id_for_project(
                entry_id=request.parent_id,
                project_id=project.id,
            )

            if parent is None:
                raise HTTPException(status_code=404, detail="Parent folder not found")

            if parent.type != "folder":
                raise HTTPException(status_code=422, detail="Parent must be a folder")

        new_file = await file_repository.create_entry(
            project_id=project.id,
            parent_id=request.parent_id,
            name=request.name,
            entry_type=request.type,
            content=request.content
        )
        if new_file is None:
            raise HTTPException(
                status_code=409,
                detail="A file or folder with that name already exists here",
            )

    return FileEntryResponse.model_validate(new_file)
