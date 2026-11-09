#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path

from run_public import Client


def expect(client: Client, sql: str, wanted: list[str]) -> None:
    actual = client.execute(sql)
    if actual != wanted:
        raise AssertionError(f"{sql}: expected {wanted!r}, got {actual!r}")


def kill(client: Client) -> None:
    assert client.process is not None
    client.process.kill()
    client.process.wait(timeout=10)
    client.process = None


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="mvd-crash-") as tmp:
        directory = Path(tmp)
        client = Client(directory)
        try:
            expect(
                client,
                "CREATE TABLE docs (id BIGINT PRIMARY KEY, content VARCHAR(16), v VECTOR(2))",
                ["OK"],
            )
            expect(
                client,
                "INSERT INTO docs VALUES (1, 'one', '[1,0]'), (2, 'two', '[0,1]')",
                ["OK 2"],
            )
            expect(client, "BEGIN", ["OK"])
            expect(client, "UPDATE docs SET content = 'changed' WHERE id = 1", ["OK 1"])
            expect(client, "DELETE FROM docs WHERE id = 2", ["OK 1"])
            kill(client)
            client.start()
            expect(
                client,
                "SELECT id, content FROM docs ORDER BY id",
                ["1\tone", "2\ttwo"],
            )

            expect(client, "BEGIN", ["OK"])
            expect(client, "INSERT INTO docs VALUES (3, 'three', '[2,0]')", ["OK 1"])
            expect(client, "COMMIT", ["OK"])
            kill(client)
            client.start()
            expect(
                client,
                "SELECT id FROM docs ORDER BY id",
                ["1", "2", "3"],
            )
        finally:
            client.stop()

        journal = directory / "journal.ndjson"
        with journal.open("ab") as fh:
            fh.write(b'{"tx":["INSERT INTO docs VALUES (99')
        client = Client(directory)
        try:
            expect(
                client,
                "SELECT id FROM docs ORDER BY id",
                ["1", "2", "3"],
            )
        finally:
            client.stop()
        print("PASS crash recovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
