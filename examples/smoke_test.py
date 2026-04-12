#!/usr/bin/env python3
"""Manual smoke test against a real KCFinder instance.

Usage:
    Set KCFINDER_USERNAME and KCFINDER_PASSWORD, then run:

        KCFINDER_USERNAME=... KCFINDER_PASSWORD=... uv run python examples/smoke_test.py

    The remaining env vars are loaded from .env in the project root.
    Review the output to verify request/response behavior.
"""

import asyncio
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from kcfinder_client import ActionError, AsyncKCFinderClient, harmonysite_auth_from_env


async def main() -> None:
    load_dotenv()
    auth = harmonysite_auth_from_env()
    browse_url = os.environ["KCFINDER_BROWSE_URL"]

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
        try:
            await client.create_dir("", test_dir)
            print("  Created")
        except ActionError:
            print("  Already exists (reusing)")

        # Valid 1x1 white JPEG (generated with Pillow)
        import base64

        jpeg_b64 = (
            "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJ"
            "CQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcp"
            "LDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwh"
            "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIy"
            "MjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QA"
            "HwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAA"
            "AgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKB"
            "kaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6"
            "Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWG"
            "h4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG"
            "x8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QA"
            "HwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREA"
            "AgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEI"
            "FEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5"
            "OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOE"
            "hYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPE"
            "xcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oA"
            "DAMBAAIRAxEAPwD3+iiigD//2Q=="
        )
        with tempfile.NamedTemporaryFile(
            suffix=".jpg", delete=False
        ) as f:
            f.write(base64.b64decode(jpeg_b64))
            test_file = Path(f.name)

        print(f"\n=== Upload: {test_file.name} ===")
        await client.upload(test_dir, test_file)
        print("  Uploaded")

        print(f"\n=== List files in {test_dir} ===")
        files = await client.list_files(test_dir)
        for f in files:
            print(f"  {f.name} ({f.size} bytes)")

        print(f"\n=== Download: {files[0].name} ===")
        content = await client.download(test_dir, files[0].name)
        print(f"  Got {len(content)} bytes")

        print(f"\n=== Delete file: {files[0].name} ===")
        await client.delete(test_dir, files[0].name)
        print("  Deleted")

        print(f"\n=== Delete dir: {test_dir} ===")
        try:
            await client.delete_dir(test_dir)
            print("  Deleted")
        except ActionError as e:
            print(f"  Failed: {e.message}")
            print("  (Server config may restrict directory deletion)")

        test_file.unlink()
        print("\n=== Smoke test complete ===")


if __name__ == "__main__":
    asyncio.run(main())
