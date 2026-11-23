import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.mark.parametrize(
    ("suffix", "status_code"), [("", 200), ("a", 422)], ids=["at-limit", "over-limit"]
)
def test_explain_file_source_limit(project_client, monkeypatch, suffix, status_code):
    from app.ai import router as ai_router

    async def run_test():
        async with project_client() as (client, project_id):
            files_url = f"/projects/{project_id}/files"
            source = "é" * 4096 + suffix
            created = await client.post(
                files_url, json={"name": "sample.py", "type": "file", "content": source}
            )
            assert created.status_code == 201, created.text
            file = created.json()
            invoke = AsyncMock(return_value={"explanation": "test explanation"})
            graph_factory = Mock(return_value=SimpleNamespace(ainvoke=invoke))
            monkeypatch.setattr(ai_router, "get_explain_graph", graph_factory)

            response = await client.post(f"{files_url}/{file['id']}/explain")
            assert response.status_code == status_code, response.text
            if status_code == 422:
                assert "8 KiB limit" in response.json()["detail"]
                graph_factory.assert_not_called()
            else:
                graph_factory.assert_called_once()
                invoke.assert_awaited_once_with({"name": "sample.py", "content": source})
                assert response.json() == {
                    "explanation": "test explanation",
                    "revision": file["revision"],
                }

    asyncio.run(run_test())


def test_explain_file_returns_gateway_timeout(project_client, monkeypatch):
    from app.ai import router as ai_router

    async def run_test():
        cancelled = asyncio.Event()

        async def slow_graph(_state):
            try:
                await asyncio.Future()
            finally:
                cancelled.set()

        graph = SimpleNamespace(ainvoke=AsyncMock(side_effect=slow_graph))
        monkeypatch.setattr(ai_router, "EXPLAIN_TIMEOUT_SECONDS", 0.05)
        monkeypatch.setattr(ai_router, "get_explain_graph", lambda: graph)

        async with project_client() as (client, project_id):
            files_url = f"/projects/{project_id}/files"
            created = await client.post(
                files_url, json={"name": "sample.py", "type": "file", "content": "pass"}
            )
            assert created.status_code == 201, created.text
            response = await client.post(f"{files_url}/{created.json()['id']}/explain")
            assert response.status_code == 504, response.text
            assert response.json()["detail"] == "AI took longer than expected"
            graph.ainvoke.assert_awaited_once()
            assert cancelled.is_set()

    asyncio.run(run_test())
