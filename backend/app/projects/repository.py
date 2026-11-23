from sqlalchemy import select,func,update

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.projects.model import Project
from app.users.model import User


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_project(self, name: str, owner_id: UUID) -> Project:
        new_project = Project(name=name,owner_id = owner_id)
        self.session.add(new_project)
        await self.session.flush()
        return new_project

    async def list_by_owner(self, owner_id: UUID) -> list[Project]:
        result = await self.session.execute(
            select(Project).where(Project.owner_id == owner_id).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_for_clerk_user(
        self, project_id: UUID, clerk_user_id: str, *, for_update: bool = False
    ) -> Project | None:
        statement = (
            select(Project)
            .join(User, User.id == Project.owner_id)
            .where(Project.id == project_id, User.clerk_user_id == clerk_user_id)
        )
        if for_update:
            statement = statement.with_for_update(of=Project)
        return await self.session.scalar(statement)

    async def rename_for_owner(self,project_id: UUID,owner_id:UUID, new_name:str) -> Project | None:
        result = await self.session.execute(
            update(Project)
            .where(Project.id == project_id, Project.owner_id == owner_id)
            .values(name=new_name,updated_at=func.now())
            .returning(Project)
        )
        return result.scalar_one_or_none()
