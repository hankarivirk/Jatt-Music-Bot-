"""
Run this script once to generate your ASSISTANT_SESSION string.
Usage: python genstring.py
"""

import asyncio

from pyrogram import Client

API_ID = input("Enter your API_ID: ").strip()
API_HASH = input("Enter your API_HASH: ").strip()

print("\nEnter the phone number of the ASSISTANT account when prompted.\n")

app = Client(":memory:", api_id=int(API_ID), api_hash=API_HASH)


async def main():
    await app.start()
    session = await app.export_session_string()
    print("\n" + "=" * 60)
    print("YOUR ASSISTANT_SESSION STRING (keep this secret!):")
    print("=" * 60)
    print(f"\n{session}\n")
    print("=" * 60)
    print("Copy the string above and set it as ASSISTANT_SESSION in your .env")
    await app.stop()


asyncio.run(main())
