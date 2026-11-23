import asyncio


def test_folder_listing_omits_file_content(project_client):
    async def run_test():
        async with project_client() as (client, project_id):
            files_url = f"/projects/{project_id}/files"
            source = "print(5)"
            created = await client.post(
                files_url,
                json={"name": "sample.py", "type": "file", "content": source},
            )
            assert created.status_code == 201, created.text
            file = created.json()

            listing = await client.get(files_url)
            assert listing.status_code == 200, listing.text
            (entry,) = listing.json()
            assert entry["id"] == file["id"]
            assert entry["revision"] == file["revision"]
            assert "content" not in entry

            opened = await client.get(f"{files_url}/{file['id']}")
            assert opened.status_code == 200, opened.text
            assert opened.json()["content"] == source

    asyncio.run(run_test())
