#!/usr/bin/env python3
"""Dump raw KCFinder responses to understand the real protocol."""

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from kcfinder_client._core import build_action_url, build_headers
from kcfinder_client.auth import harmonysite_auth_from_env

import httpx


async def main() -> None:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    auth = harmonysite_auth_from_env()
    browse_url = os.environ["KCFINDER_BROWSE_URL"]

    async with httpx.AsyncClient() as client:
        # Step 1: Login
        print("=== Step 1: Login POST ===")
        login_resp = await client.post(
            os.environ["KCFINDER_LOGIN_URL"],
            data={
                "username": os.environ["KCFINDER_USERNAME"],
                "password": os.environ["KCFINDER_PASSWORD"],
            },
        )
        print(f"Status: {login_resp.status_code}")
        print(f"Cookies after login: {dict(client.cookies)}")
        print(f"Response body (first 500): {login_resp.text[:500]}")

        # Step 2: Init KCFinder session
        print("\n=== Step 2: KCFinder session init GET ===")
        init_url = auth._init_url()
        print(f"Init URL: {init_url[:200]}...")
        init_resp = await client.get(init_url)
        print(f"Status: {init_resp.status_code}")
        print(f"Cookies after init: {dict(client.cookies)}")
        print(f"Response body (first 500): {init_resp.text[:500]}")

        # Step 3: Try chDir
        print("\n=== Step 3: chDir POST ===")
        headers = build_headers(auth.get_referer())
        url = build_action_url(browse_url, "chDir", "images")
        resp = await client.post(url, data={"dir": ""}, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:1000]}")

        # Step 4: Try init
        print("\n=== Step 4: init POST ===")
        url = build_action_url(browse_url, "init", "images")
        resp = await client.post(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:1000]}")


if __name__ == "__main__":
    asyncio.run(main())
