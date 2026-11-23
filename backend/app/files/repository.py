from typing import Literal
from uuid import UUID
from sqlalchemy.orm import aliased

from sqlalchemy import select,update,func,delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import RowMapping

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
        entry = await self.session.scalar(statement)
        if entry is not None:
            await self._bump_ancestor_revisions(project_id, entry.parent_id)
        return entry

    async def get_project_usage(self, project_id: UUID) -> tuple[int, int]:
        result = await self.session.execute(
            select(
                func.count(FileEntry.id),
                func.coalesce(
                    func.sum(func.octet_length(func.convert_to(FileEntry.content, "UTF8"))),
                    0,
                ),
            ).where(FileEntry.project_id == project_id)
        )
        entries, content_bytes = result.one()
        return entries, content_bytes

    async def get_file_content_size(self, project_id: UUID, entry_id: UUID) -> int | None:
        return await self.session.scalar(
            select(
                func.coalesce(
                    func.octet_length(func.convert_to(FileEntry.content, "UTF8")), 0
                )
            ).where(
                FileEntry.project_id == project_id,
                FileEntry.id == entry_id,
                FileEntry.type == "file",
            )
        )

    async def list_children(
            self,
            project_id:UUID,
            parent_id:UUID | None,
    ) -> list[RowMapping]:
        query = select(
            FileEntry.id,
            FileEntry.project_id,
            FileEntry.parent_id,
            FileEntry.name,
            FileEntry.type,
            FileEntry.updated_at,
            FileEntry.revision,
        ).where(FileEntry.project_id == project_id)
        if parent_id is None:
            query = query.where(FileEntry.parent_id.is_(None))
        else:
            query = query.where(FileEntry.parent_id == parent_id)
        query = query.order_by(
            (FileEntry.type == "folder").desc(),
            FileEntry.name.asc()
        )
        children = await self.session.execute(query)
        return list(children.mappings().all())

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
        entry = result.scalar_one_or_none()
        if entry is not None:
            await self._bump_ancestor_revisions(project_id, entry.parent_id)
        return entry

    async def rename_for_project(self,entry_id:UUID,project_id:UUID,new_name:str,expected_revision: int) -> FileEntry | None:
        result = await self.session.execute(
            update(FileEntry)
            .where(FileEntry.id == entry_id , FileEntry.project_id == project_id,FileEntry.revision == expected_revision)
            .values(name=new_name, updated_at=func.now(), revision=FileEntry.revision + 1)
            .returning(FileEntry)
        )
        entry = result.scalar_one_or_none()
        if entry is not None:
            await self._bump_ancestor_revisions(project_id, entry.parent_id)
        return entry

    async def delete_for_project(self,entry_id:UUID,project_id:UUID,expected_revision: int) -> bool:
        statement = (
            delete(FileEntry)
            .where(
                FileEntry.id == entry_id,
                FileEntry.project_id == project_id,
                FileEntry.revision == expected_revision,
            )
            .returning(FileEntry.parent_id)
        )
        result = await self.session.execute(statement)
        deleted = result.one_or_none()
        if deleted is None:
            return False
        await self._bump_ancestor_revisions(project_id, deleted.parent_id)
        return True

    async def _bump_ancestor_revisions(
        self, project_id: UUID, parent_id: UUID | None
    ) -> None:
        if parent_id is None:
            return

        # File writes lock the project row before changing the tree.
        ancestors = (
            select(FileEntry.id, FileEntry.parent_id)
            .where(FileEntry.project_id == project_id, FileEntry.id == parent_id)
            .cte(recursive=True)
        )
        parent = aliased(FileEntry)
        ancestors = ancestors.union(
            select(parent.id, parent.parent_id)
            .join(ancestors, parent.id == ancestors.c.parent_id)
            .where(parent.project_id == project_id)
        )
        await self.session.execute(
            update(FileEntry)
            .where(
                FileEntry.project_id == project_id,
                FileEntry.type == "folder",
                FileEntry.id.in_(select(ancestors.c.id)),
            )
            .values(revision=FileEntry.revision + 1, updated_at=func.now())
        )
