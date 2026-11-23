import asyncio
from unittest.mock import Mock
from uuid import uuid4


def test_project_and_explain_routes_require_authentication(project_client, monkeypatch):
    from app.auth.clerk import require_clerk_user
    from app.main import app

    async def run_test():
        async with project_client() as (client, project_id):
            with monkeypatch.context() as overrides:
                overrides.delitem(app.dependency_overrides, require_clerk_user)
                project_url = f"/projects/{project_id}"
                missing_token = await client.get(project_url)
                assert missing_token.status_code == 401
                assert missing_token.headers["www-authenticate"] == "Bearer"
                assert (
                    await client.post(f"{project_url}/files/{uuid4()}/explain")
                ).status_code == 401

    asyncio.run(run_test())


def test_project_and_file_ownership(project_client, monkeypatch):
    from app.ai import router as ai_router

    async def run_test():
        graph_factory = Mock()
        monkeypatch.setattr(ai_router, "get_explain_graph", graph_factory)

        async with project_client() as (client, project_id):
            project_url = f"/projects/{project_id}"
            files_url = f"{project_url}/files"
            created = await client.post(
                files_url, json={"name": "private.py", "type": "file", "content": "pass"}
            )
            assert created.status_code == 201, created.text
            file = created.json()
            file_url = f"{files_url}/{file['id']}"

            headers = {"x-test-clerk-user": f"other-test-user-{uuid4()}"}
            bootstrap = await client.post("/auth/bootstrap", headers=headers)
            assert bootstrap.status_code == 200, bootstrap.text
            for method, url, options in (
                ("GET", project_url, {}),
                ("GET", files_url, {}),
                ("GET", file_url, {}),
                ("POST", f"{file_url}/explain", {}),
                ("DELETE", file_url, {"params": {"expected_revision": file["revision"]}}),
            ):
                response = await client.request(method, url, headers=headers, **options)
                assert response.status_code == 404, (method, url, response.text)

            other_project = await client.post("/projects", json={"name": "Second project"})
            assert other_project.status_code == 201, other_project.text
            wrong_project_file = f"/projects/{other_project.json()['id']}/files/{file['id']}"
            assert (await client.get(wrong_project_file)).status_code == 404
            assert (await client.post(f"{wrong_project_file}/explain")).status_code == 404
            graph_factory.assert_not_called()
            assert (await client.get(file_url)).status_code == 200

    asyncio.run(run_test())
