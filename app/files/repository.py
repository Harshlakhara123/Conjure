from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.files.model import FileEntry
class FileRepository:
    def __init__(self,session:AsyncSession) -> None:
        self.session = session

    async def get_by_id_for_project(self,entry_id:UUID,project_id:UUID) -> FileEntry | None:
        result = await self.session.execute(
            select(FileEntry).where(FileEntry.id == entry_id,FileEntry.project_id==project_id)
        )
        return result.scalar_one_or_none()

    async def create_entry(
        self,
        project_id: UUID,
        parent_id: UUID | None,
        name: str,
        entry_type: Literal["file", "folder"],
        content: str | None,
    ) -> FileEntry | None:
        statement = (
            insert(FileEntry)
            .values(
                project_id=project_id,
                parent_id=parent_id,
                name=name,
                type=entry_type,
                content=content,
            )
            .on_conflict_do_nothing(
                index_elements=[FileEntry.project_id, FileEntry.parent_id, FileEntry.name]
            )
            .returning(FileEntry)
        )
        return await self.session.scalar(statement)
