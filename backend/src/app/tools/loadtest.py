"""Load test: `uv run loadtest --users 20 --turns 3`.

Signs up `--users` throwaway accounts, then each sends `--turns` questions
one after another, reading every SSE stream to its end, and reopens the
last one with `connect`. Reports time to first token, turn time, connect
and history latency (p50/p95/max), throughput and errors.

Run it against a backend started with `AGENT_FAKE_MODEL=true` (no provider
cost; measures API, stream, runner, PostgreSQL, Redis) and
`REGISTRATION_ENABLED=true`. Accounts are named `load-<run>-<n>@example.com`.
"""

import argparse
import asyncio
import json
import statistics
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field

import httpx
from uuid_utils.compat import uuid7

PASSWORD = "L0ad!test-pass"


@dataclass
class Results:
    timings: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    errors: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def time(self, name: str, seconds: float) -> None:
        self.timings[name].append(seconds * 1000)


async def _stream(
    client: httpx.AsyncClient, url: str, headers: dict, payload=None
) -> tuple[float | None, list[dict]]:
    """POST an SSE route; returns (seconds to first text token, events)."""
    started = time.monotonic()
    first: float | None = None
    events = []
    async with client.stream(
        "POST", url, json=payload, headers={**headers, "Accept": "text/event-stream"}
    ) as response:
        if response.status_code != 200:
            await response.aread()
            try:
                code = response.json()["error"]["code"]
            except (ValueError, KeyError, TypeError):
                code = "unexpected"
            raise RuntimeError(f"{response.status_code} {code}")
        async for line in response.aiter_lines():
            if not line.startswith("data:"):
                continue
            event = json.loads(line[5:])
            events.append(event)
            if first is None and event["type"] == "TEXT_MESSAGE_CONTENT":
                first = time.monotonic() - started
    return first, events


async def _user(
    client: httpx.AsyncClient, run: str, index: int, turns: int, results: Results
) -> None:
    email = f"load-{run}-{index}@example.com"
    try:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "name": f"Load {index}", "password": PASSWORD},
        )
        login = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
        )
        login.raise_for_status()
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        workspaces = (await client.get("/api/v1/workspaces", headers=headers)).json()
        workspace = workspaces["data"][0]["id"]
        created = await client.post(
            f"/api/v1/workspaces/{workspace}/conversations", json={}, headers=headers
        )
        conversation = created.json()["id"]
    except Exception as error:
        results.errors[f"setup: {type(error).__name__}"] += 1
        return
    parent = None
    for turn in range(turns):
        payload = {
            "parent_message_id": parent,
            "message": {"id": str(uuid7()), "text": f"Câu hỏi số {turn}"},
        }
        started = time.monotonic()
        try:
            first, events = await _stream(
                client,
                f"/api/v1/conversations/{conversation}/messages",
                headers,
                payload,
            )
        except Exception as error:
            results.errors[f"turn: {str(error)[:60]}"] += 1
            continue
        results.time("turn", time.monotonic() - started)
        if first is not None:
            results.time("first_token", first)
        status = [e["value"] for e in events if e["type"] == "CUSTOM"]
        if not status or status[-1]["status"] != "completed":
            results.errors["turn not completed"] += 1
            continue
        parent = status[-1]["assistantMessageId"]
    started = time.monotonic()
    try:
        await _stream(client, f"/api/v1/conversations/{conversation}/connect", headers)
        results.time("connect", time.monotonic() - started)
        started = time.monotonic()
        response = await client.get(
            f"/api/v1/conversations/{conversation}/messages", headers=headers
        )
        response.raise_for_status()
        results.time("history", time.monotonic() - started)
    except Exception as error:
        results.errors[f"read: {str(error)[:60]}"] += 1


def _report(results: Results, elapsed: float, users: int, turns: int) -> None:
    print(f"\n{users} users × {turns} turns in {elapsed:.1f}s")
    done = len(results.timings["turn"])
    print(f"turns completed: {done}/{users * turns} ({done / elapsed:.2f}/s)")
    print(f"{'metric':<12} {'n':>5} {'p50 ms':>9} {'p95 ms':>9} {'max ms':>9}")
    for name in ("first_token", "turn", "connect", "history"):
        values = sorted(results.timings[name])
        if not values:
            continue
        p95 = values[min(len(values) - 1, int(len(values) * 0.95))]
        print(
            f"{name:<12} {len(values):>5} {statistics.median(values):>9.0f} "
            f"{p95:>9.0f} {values[-1]:>9.0f}"
        )
    print("errors:", dict(results.errors) or "none")


async def _main(base_url: str, users: int, turns: int) -> None:
    run = uuid.uuid4().hex[:8]
    results = Results()
    limits = httpx.Limits(max_connections=users * 2 + 10)
    async with httpx.AsyncClient(
        base_url=base_url, timeout=120, limits=limits
    ) as client:
        started = time.monotonic()
        await asyncio.gather(
            *(_user(client, run, i, turns, results) for i in range(users))
        )
        _report(results, time.monotonic() - started, users, turns)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--users", type=int, default=20)
    parser.add_argument("--turns", type=int, default=3)
    args = parser.parse_args()
    asyncio.run(_main(args.base_url, args.users, args.turns))


if __name__ == "__main__":
    main()
