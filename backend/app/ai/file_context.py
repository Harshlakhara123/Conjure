from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.files.repository import FileRepository
@dataclass(frozen=True)
class FileContext:
    name:str
    content:str
    revision:int

async def load_file_context(
        session:AsyncSession,
        project_id:UUID,
        entry_id:UUID
    ) -> FileContext | None:
    entry = await FileRepository(session).get_by_id_for_project(
        entry_id=entry_id,
        project_id=project_id,
    )
    if entry is None:
        return None
    if entry.type != "file":
        return None
    return FileContext(
        name=entry.name,
        content=entry.content or "",
        revision=entry.revision
    )
