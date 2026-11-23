import asyncio


def test_project_quotas_reject_growth_and_preserve_saved_content(project_client, monkeypatch):
    from app.files import quotas

    monkeypatch.setattr(quotas, "MAX_PROJECT_ENTRIES", 2)
    monkeypatch.setattr(quotas, "MAX_PROJECT_CONTENT_BYTES", 4)

    async def run_test():
        async with project_client() as (client, project_id):
            files_url = f"/projects/{project_id}/files"
            folder = await client.post(files_url, json={"name": "src", "type": "folder"})
            assert folder.status_code == 201, folder.text

            body = {"name": "sample.py", "type": "file", "parent_id": folder.json()["id"]}
            large = await client.post(files_url, json={**body, "content": "ééa"})
            assert large.status_code == 409 and "byte limit" in large.json()["detail"]
            created = await client.post(files_url, json={**body, "content": "éé"})
            assert created.status_code == 201, created.text
            file = created.json()
            file_url = f"{files_url}/{file['id']}"

            extra = await client.post(files_url, json={"name": "extra.py", "type": "file"})
            assert extra.status_code == 409 and "files and folders" in extra.json()["detail"]
            oversized = await client.patch(
                f"{file_url}/content",
                json={"content": "ééa", "expected_revision": file["revision"]},
            )
            assert oversized.status_code == 409 and "byte limit" in oversized.json()["detail"]
            stored = await client.get(file_url)
            assert stored.status_code == 200, stored.text
            assert stored.json()["content"] == "éé"
            assert stored.json()["revision"] == file["revision"]
            stored_folder = await client.get(f"{files_url}/{folder.json()['id']}")
            assert stored_folder.status_code == 200, stored_folder.text
            assert stored_folder.json()["revision"] == folder.json()["revision"] + 1

            # An existing project can still shrink after its quota is lowered.
            monkeypatch.setattr(quotas, "MAX_PROJECT_CONTENT_BYTES", 1)
            shrunk = await client.patch(
                f"{file_url}/content",
                json={"content": "éa", "expected_revision": file["revision"]},
            )
            assert shrunk.status_code == 200, shrunk.text

    asyncio.run(run_test())
