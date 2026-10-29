"""Print the FastAPI OpenAPI document: `uv run openapi > openapi.json`.

The frontend generates its API types from this output (`pnpm generate:api`),
so the contract comes from the code without a running server.
"""

import json


def main() -> None:
    from app.main import app

    print(json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
