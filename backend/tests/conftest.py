import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import pytest
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
def project_client(monkeypatch):
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL test.")

    from app.auth.clerk import require_clerk_user
    from app.db_session import get_db_session
    from app.main import app
    from app.projects.repository import ProjectRepository
    from app.users.repository import UserRepository

    @asynccontextmanager
    async def open_client() -> AsyncIterator[tuple[AsyncClient, UUID]]:
        engine = create_async_engine(database_url)
        clerk_id = f"file-test-{uuid4()}"

        try:
            async with engine.connect() as connection:
                transaction = await connection.begin()
                sessions = async_sessionmaker(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                )

                async def override_db_session():
                    async with sessions() as session:
                        yield session

                def override_clerk_user(request: Request) -> str:
                    return request.headers.get("x-test-clerk-user", clerk_id)

                try:
                    async with sessions.begin() as session:
                        user = await UserRepository(session).get_or_create(clerk_id)
                        project = await ProjectRepository(session).create_project(
                            name="File regression test",
                            owner_id=user.id,
                        )
                        project_id = project.id

                    with monkeypatch.context() as overrides:
                        overrides.setitem(
                            app.dependency_overrides,
                            require_clerk_user,
                            override_clerk_user,
                        )
                        overrides.setitem(
                            app.dependency_overrides,
                            get_db_session,
                            override_db_session,
                        )
                        async with AsyncClient(
                            transport=ASGITransport(app=app),
                            base_url="http://test",
                        ) as client:
                            yield client, project_id
                finally:
                    await transaction.rollback()
        finally:
            await engine.dispose()

    return open_client
