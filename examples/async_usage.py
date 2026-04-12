"""Async client usage examples for kcfinder-client.

Same operations as sync_usage.py but using the async client,
suitable for asyncio applications.
"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from kcfinder_client import AsyncKCFinderClient, harmonysite_auth_from_env

load_dotenv()


async def main() -> None:
    auth = harmonysite_auth_from_env()
    browse_url = auth._browse_url

    async with AsyncKCFinderClient(browse_url, auth) as client:
        # List files in the root directory
        files = await client.list_files()
        for f in files:
            print(f"{f.name}  {f.size} bytes  {f.timestamp}")

        # Upload a file
        await client.upload("", Path("image.jpg"))

        # Download a file
        data = await client.download("", "image.jpg")
        Path("downloaded.jpg").write_bytes(data)

        # Rename, delete, directory ops — all the same methods, just awaited
        await client.rename("", "image.jpg", "renamed.jpg")
        await client.delete("", "renamed.jpg")
        await client.create_dir("", "new-folder")
        await client.delete_dir("new-folder")


if __name__ == "__main__":
    asyncio.run(main())
