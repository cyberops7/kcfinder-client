#!/usr/bin/env python3
"""Manual smoke test against a real KCFinder instance.

Usage:
    Set environment variables (see kcfinder_client.auth.harmonysite_auth_from_env),
    then run:

        uv run python examples/smoke_test.py

    This will exercise the main client operations against the real instance.
    Review the output to verify request/response behavior.
"""

import asyncio
import tempfile
from pathlib import Path

from kcfinder_client import AsyncKCFinderClient, harmonysite_auth_from_env


async def main() -> None:
    auth = harmonysite_auth_from_env()
    browse_url = "https://www.witnessmusicutah.org/brostools/jquery/kcfinder/browse.php"

    async with AsyncKCFinderClient(browse_url, auth) as client:
        # List files in root
        print("=== List files in root ===")
        files = await client.list_files("")
        for f in files:
            print(f"  {f.name} ({f.size} bytes, {f.mtime})")

        # Get full tree
        print("\n=== Directory tree ===")
        tree = await client.get_tree()
        print(
            f"  Root: {tree.name} "
            f"({len(tree.children)} subdirs, {len(tree.files)} files)"
        )
        for child in tree.children:
            print(f"    {child.name}/")

        # Create a test directory, upload a file, list, then clean up
        test_dir = "_smoke_test_temp"
        print(f"\n=== Create dir: {test_dir} ===")
        await client.create_dir("", test_dir)

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"smoke test content")
            test_file = Path(f.name)

        print(f"=== Upload: {test_file.name} ===")
        await client.upload(test_dir, test_file)

        print(f"=== List files in {test_dir} ===")
        files = await client.list_files(test_dir)
        for f in files:
            print(f"  {f.name} ({f.size} bytes)")

        print(f"=== Download: {files[0].name} ===")
        content = await client.download(test_dir, files[0].name)
        print(f"  Got {len(content)} bytes")

        print(f"=== Delete: {files[0].name} ===")
        await client.delete(test_dir, files[0].name)

        print(f"=== Delete dir: {test_dir} ===")
        await client.delete_dir(test_dir)

        test_file.unlink()
        print("\n=== Smoke test complete ===")


if __name__ == "__main__":
    asyncio.run(main())
