import asyncio


def test_stale_rename_keeps_last_successful_name(project_client):
    async def run_test():
        async with project_client() as (client, project_id):
            files_url = f"/projects/{project_id}/files"
            created = await client.post(
                files_url,
                json={"name": "original.py", "type": "file"},
            )
            assert created.status_code == 201, created.text
            file = created.json()
            revision = file["revision"]
            file_url = f"{files_url}/{file['id']}"

            renamed = await client.patch(
                f"{file_url}/name",
                json={"name": "renamed.py", "expected_revision": revision},
            )
            assert renamed.status_code == 200, renamed.text
            assert renamed.json()["revision"] == revision + 1

            stale = await client.patch(
                f"{file_url}/name",
                json={"name": "stale.py", "expected_revision": revision},
            )
            assert stale.status_code == 409, stale.text

            current = await client.get(file_url)
            assert current.status_code == 200, current.text
            assert current.json()["name"] == "renamed.py"
            assert current.json()["revision"] == revision + 1

    asyncio.run(run_test())
