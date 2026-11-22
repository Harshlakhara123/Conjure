from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.users.repository import UserRepository
from app.projects.repository import ProjectRepository
from app.files.repository import FileRepository
@dataclass(frozen=True)
class FileContext:
    name:str
    content:str
    revision:int

async def load_file_context(
        session:AsyncSession,
        clerk_user_id:str,
        project_id:UUID,
        entry_id:UUID
    ) -> FileContext | None:
    user = await UserRepository(session).get_by_clerk_id(clerk_user_id)
    if user is None:
        return None
    project = await ProjectRepository(session).get_by_id_for_owner(
        project_id=project_id,
        owner_id=user.id
    )
    if project is None:
        return None
    entry = await FileRepository(session).get_by_id_for_project(
        entry_id=entry_id,
        project_id=project.id,
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