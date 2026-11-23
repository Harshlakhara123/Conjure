from uuid import UUID

from fastapi import HTTPException

from app.files.repository import FileRepository

MAX_PROJECT_ENTRIES = 1000
MAX_PROJECT_CONTENT_BYTES = 20 * 1024 * 1024


async def require_project_capacity(
    repository: FileRepository, project_id: UUID, *, adding_entry: bool = False
) -> None:
    entries, content_bytes = await repository.get_project_usage(project_id)
    if adding_entry and entries > MAX_PROJECT_ENTRIES:
        raise HTTPException(
            status_code=409,
            detail=f"A project can contain at most {MAX_PROJECT_ENTRIES} files and folders.",
        )
    if content_bytes > MAX_PROJECT_CONTENT_BYTES:
        raise HTTPException(
            status_code=409,
            detail=f"Project content exceeds the {MAX_PROJECT_CONTENT_BYTES}-byte limit.",
        )
