"""Sync client usage examples for kcfinder-client.

Demonstrates common operations: listing files, uploading,
downloading, and directory management using the sync client.

Requires environment variables for HarmonySite auth (see .env.example),
or substitute SessionAuth if using a standard KCFinder install.
"""

from pathlib import Path

from dotenv import load_dotenv

from kcfinder_client import KCFinderClient, harmonysite_auth_from_env

load_dotenv()


def main() -> None:
    auth = harmonysite_auth_from_env()
    browse_url = auth._browse_url

    with KCFinderClient(browse_url, auth) as client:
        # List files in the root directory
        files = client.list_files()
        for f in files:
            print(f"{f.name}  {f.size} bytes  {f.timestamp}")

        # List files in a subdirectory
        files = client.list_files("photos")

        # Upload a file to the root directory
        client.upload("", Path("image.jpg"))

        # Upload multiple files at once
        client.upload("photos", [Path("a.jpg"), Path("b.jpg")])

        # Download a file
        data = client.download("", "image.jpg")
        Path("downloaded.jpg").write_bytes(data)

        # Get a thumbnail (returned as PNG bytes)
        thumb = client.get_thumbnail("", "image.jpg")
        Path("thumb.png").write_bytes(thumb)

        # Rename and delete
        client.rename("", "image.jpg", "renamed.jpg")
        client.delete("", "renamed.jpg")

        # Directory operations
        client.create_dir("", "new-folder")
        client.rename_dir("new-folder", "my-folder")
        client.delete_dir("my-folder")

        # Browse the directory tree
        tree = client.get_tree()
        print(f"Root: {tree.name} ({tree.has_subdirs} subdirs)")
        subdirs = client.expand("")
        for d in subdirs:
            print(f"  {d.name}/")


if __name__ == "__main__":
    main()
