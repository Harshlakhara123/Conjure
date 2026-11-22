from fastapi import APIRouter , Depends , HTTPException , Response
from uuid import UUID
from typing import Annotated
from app.auth.clerk import require_clerk_user
from app.db_session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.users.repository import UserRepository
from app.projects.repository import ProjectRepository
from app.files.repository import FileRepository

from app.files.schemas import FileEntryResponse,FileEntryCreate,FileContentUpdate,FileEntryRename
router = APIRouter(prefix='/projects/{project_id}/files')

MAX_FILE_CONTENT_BYTES = 1024 * 1024
def validate_file_content_size(content:str | None) -> None:
    if content is None:
        return
    if len(content.encode("utf-8")) > MAX_FILE_CONTENT_BYTES:
        raise HTTPException(status_code=413,detail="File content exceeds the 1 MiB limit.")
@router.post("",response_model=FileEntryResponse,status_code=201)
async def create_file(
    request:FileEntryCreate,
    project_id:UUID,
    clerk_user_id: Annotated[str, Depends(require_clerk_user)],
    session:Annotated[AsyncSession, Depends(get_db_session)],
) -> FileEntryResponse:
    validate_file_content_size(request.content)
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

@router.get("",response_model=list[FileEntryResponse])
async def list_children(
    project_id:UUID,
    clerk_user_id: Annotated[str, Depends(require_clerk_user)],
    session:Annotated[AsyncSession, Depends(get_db_session)],
    parent_id:UUID | None = None
) -> list[FileEntryResponse]:
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
        if parent_id is not None:
            parent = await file_repository.get_by_id_for_project(
                entry_id=parent_id,
                project_id=project_id
            )
            if parent is None:
                raise HTTPException(status_code=404, detail="Parent folder not found")
            if parent.type == "file":
                raise HTTPException(status_code=422, detail="Parent must be a folder")
        children = await file_repository.list_children(
            project_id=project_id,
            parent_id=parent_id
        )
        return [FileEntryResponse.model_validate(entry) for entry in children]


@router.get("/{entry_id}",response_model=FileEntryResponse)
async def get_content_by_file_id(
    project_id:UUID,
    entry_id:UUID,
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
        entry = await FileRepository(session).get_by_id_for_project(
            entry_id=entry_id,
            project_id=project_id
        )
        if entry is None:
            raise HTTPException(status_code=404, detail="file entry not found")

        return FileEntryResponse.model_validate(entry)


@router.patch("/{entry_id}/content",response_model=FileEntryResponse)
async def update_content(
    request: FileContentUpdate,
    project_id:UUID,
    entry_id:UUID,
    clerk_user_id: Annotated[str, Depends(require_clerk_user)],
    session:Annotated[AsyncSession,Depends(get_db_session)],
) -> FileEntryResponse:
    validate_file_content_size(request.content)
    async with session.begin():
        user = await UserRepository(session).get_by_clerk_id(clerk_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        project = await ProjectRepository(session).get_by_id_for_owner(
            project_id=project_id,
            owner_id=user.id
        )
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")

        file_repository = FileRepository(session)
        updated_file = await file_repository.update_content_for_project(
            entry_id=entry_id,
            project_id=project.id,
            content=request.content,
            expected_revision=request.expected_revision,
        )
        if updated_file is None:
            current_entry = await file_repository.get_by_id_for_project(
                entry_id=entry_id,
                project_id=project.id,
            )
            if current_entry is None or current_entry.type != "file":
                raise HTTPException(status_code=404, detail="Text file not found")
            raise HTTPException(
                status_code=409,
                detail="File has changed. Reload it before saving again.",
            )

    return FileEntryResponse.model_validate(updated_file)

@router.patch("/{entry_id}/name",response_model=FileEntryResponse)
async def update_name(
    request:FileEntryRename,
    project_id:UUID,
    entry_id:UUID,
    clerk_user_id: Annotated[str, Depends(require_clerk_user)],
    session:Annotated[AsyncSession,Depends(get_db_session)],
) -> FileEntryResponse:
    try:
        async with session.begin():
            user = await UserRepository(session).get_by_clerk_id(clerk_user_id)
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            project = await ProjectRepository(session).get_by_id_for_owner(
                project_id=project_id,
                owner_id=user.id
            )
            if project is None:
                raise HTTPException(status_code=404, detail="Project not found")

            file_repository = FileRepository(session)
            file_with_updated_name = await file_repository.rename_for_project(
                entry_id=entry_id,
                project_id=project_id,
                new_name=request.name,
                expected_revision=request.expected_revision,
            )
            if file_with_updated_name is None:
                current_entry = await file_repository.get_by_id_for_project(
                    entry_id=entry_id,
                    project_id=project_id,
                )
                if current_entry is None:
                    raise HTTPException(status_code=404, detail="file not found")
                raise HTTPException(
                    status_code=409,
                    detail="This entry changed. Reload it before renaming.",
                )
    except IntegrityError as exc:
        driver_error = getattr(exc.orig, "__cause__", None)
        constraint_name = getattr(driver_error, "constraint_name", None)
        if constraint_name == "uq_files_sibling_name":
            raise HTTPException(
                status_code=409,
                detail="A file or folder with that name already exists"
            ) from exc
        raise

    return FileEntryResponse.model_validate(file_with_updated_name)

@router.delete("/{entry_id}",status_code=204)
async def delete_file(
    project_id:UUID,
    entry_id:UUID,
    clerk_user_id: Annotated[str, Depends(require_clerk_user)],
    session:Annotated[AsyncSession,Depends(get_db_session)],
):
    async with session.begin():
        user = await UserRepository(session).get_by_clerk_id(clerk_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        project = await ProjectRepository(session).get_by_id_for_owner(
            project_id=project_id,
            owner_id=user.id
        )
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")

        result = await FileRepository(session).delete_for_project(
            entry_id=entry_id,
            project_id=project_id
        )
        if not result:
            raise HTTPException(status_code=404,detail="File entry not found")
    return Response(status_code=204)
