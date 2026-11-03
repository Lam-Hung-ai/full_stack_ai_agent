"""Identity and access commands: `uv run iam sync-permissions`.

Run after `dbmate up` on every deployment. Organizations created before a
permission exists do not receive it automatically (database decisions: an
organization uses only what it has granted).
"""

import argparse
import asyncio


async def _sync_permissions() -> None:
    from app.database.session import SessionLocal, engine
    from app.modules.authorization.service import AuthorizationService

    try:
        async with SessionLocal() as session:
            await AuthorizationService(session).sync_catalog()
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["sync-permissions"])
    parser.parse_args()
    asyncio.run(_sync_permissions())
    print("✓ Permission catalog synchronized")


if __name__ == "__main__":
    main()
