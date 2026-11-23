import asyncio


def test_stale_delete_preserves_newer_file_content(project_client):
    async def run_test():
        async with project_client() as (client, project_id):
            files_url = f"/projects/{project_id}/files"
            created = await client.post(
                files_url,
                json={"name": "sample.py", "type": "file", "content": "print(1)"},
            )
            assert created.status_code == 201, created.text
            file = created.json()
            original_revision = file["revision"]
            file_url = f"{files_url}/{file['id']}"

            new_content = "print(2)"
            saved = await client.patch(
                f"{file_url}/content",
                json={
                    "content": new_content,
                    "expected_revision": original_revision,
                },
            )
            assert saved.status_code == 200, saved.text
            current_revision = saved.json()["revision"]
            assert current_revision == original_revision + 1

            stale = await client.delete(
                file_url, params={"expected_revision": original_revision}
            )
            assert stale.status_code == 409, stale.text

            current = await client.get(file_url)
            assert current.status_code == 200, current.text
            assert current.json()["content"] == new_content
            assert current.json()["revision"] == current_revision

            deleted = await client.delete(
                file_url, params={"expected_revision": current_revision}
            )
            assert deleted.status_code == 204, deleted.text
            missing = await client.get(file_url)
            assert missing.status_code == 404, missing.text

    asyncio.run(run_test())


def test_stale_folder_delete_preserves_edited_descendant(project_client):
    async def run_test():
        async with project_client() as (client, project_id):
            files_url = f"/projects/{project_id}/files"

            async def create(name, kind, parent_id=None):
                response = await client.post(
                    files_url, json={"name": name, "type": kind, "parent_id": parent_id}
                )
                assert response.status_code == 201, response.text
                return response.json()

            folder = await create("src", "folder")
            nested = await create("nested", "folder", folder["id"])
            file = await create("sample.py", "file", nested["id"])
            folder_url = f"{files_url}/{folder['id']}"
            file_url = f"{files_url}/{file['id']}"
            listed = await client.get(files_url)
            assert listed.status_code == 200, listed.text
            (summary,) = listed.json()
            assert summary["id"] == folder["id"]
            assert summary["revision"] == folder["revision"] + 2

            saved = await client.patch(
                f"{file_url}/content",
                json={"content": "print(5)", "expected_revision": file["revision"]},
            )
            assert saved.status_code == 200, saved.text
            stale = await client.delete(
                folder_url, params={"expected_revision": summary["revision"]}
            )
            assert stale.status_code == 409, stale.text

            current_file = await client.get(file_url)
            assert current_file.status_code == 200, current_file.text
            assert current_file.json()["content"] == "print(5)"
            current_folder = await client.get(folder_url)
            assert current_folder.status_code == 200, current_folder.text
            revision = current_folder.json()["revision"]
            assert revision == summary["revision"] + 1
            deleted = await client.delete(
                folder_url, params={"expected_revision": revision}
            )
            assert deleted.status_code == 204, deleted.text
            assert (await client.get(file_url)).status_code == 404

    asyncio.run(run_test())
