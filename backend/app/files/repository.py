from typing import Literal
from uuid import UUID

from sqlalchemy import select,update,func,delete
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

    async def list_children(
            self,
            project_id:UUID,
            parent_id:UUID | None,
    ) -> list[FileEntry]:
        query = select(FileEntry).where(FileEntry.project_id == project_id)
        if parent_id is None:
            query = query.where(FileEntry.parent_id.is_(None))
        else:
            query = query.where(FileEntry.parent_id == parent_id)
        query = query.order_by(
            (FileEntry.type == "folder").desc(),
            FileEntry.name.asc()
        )
        children = await self.session.execute(query)
        return list(children.scalars().all())

    async def update_content_for_project(
        self,
        entry_id: UUID,
        project_id: UUID,
        content: str,
        expected_revision: int,
    ) -> FileEntry | None:
        result = await self.session.execute(
            update(FileEntry)
            .where(
                FileEntry.id == entry_id,
                FileEntry.project_id == project_id,
                FileEntry.type == "file",
                FileEntry.revision == expected_revision,
            )
            .values(content=content, updated_at=func.now(), revision=FileEntry.revision + 1)
            .returning(FileEntry)
        )
        return result.scalar_one_or_none()

    async def rename_for_project(self,entry_id:UUID,project_id:UUID,new_name:str) -> FileEntry | None:
        result = await self.session.execute(
            update(FileEntry)
            .where(FileEntry.id == entry_id , FileEntry.project_id == project_id)
            .values(name=new_name, updated_at=func.now(), revision=FileEntry.revision + 1)
            .returning(FileEntry)
        )
        return result.scalar_one_or_none()

    async def delete_for_project(self,entry_id:UUID,project_id:UUID) -> bool:
        statement = delete(FileEntry).where(FileEntry.id == entry_id , FileEntry.project_id == project_id).returning(FileEntry.id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None
