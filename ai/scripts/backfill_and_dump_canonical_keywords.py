from __future__ import annotations

import asyncio
import argparse
import sys
from collections.abc import Awaitable, Callable
from datetime import datetime

from app.db.postgres import dispose_engine
from scripts.backfill_utils import (
    load_all_rows,
    load_rows,
    run_embedding_backfill,
    update_embedding_rows,
)
from app.services.canonical_keyword_resolver import (
    build_canonical_keyword_resolver_service,
)

BATCH_SIZE = 32


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill canonical keyword embeddings and dump INSERT SQL.",
    )
    parser.add_argument(
        "--ids",
        nargs="*",
        type=int,
        help="Optional canonical keyword ids to backfill and dump.",
    )
    return parser.parse_args()


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


async def _load_rows(offset: int, limit: int) -> list[dict[str, object]]:
    return await load_rows(
        table_name="canonical_keywords",
        select_columns="id, code, display_name, created_at",
        order_by="id ASC",
        offset=offset,
        limit=limit,
    )


async def _update_rows(rows: list[dict[str, object]], embeddings: list[list[float]]) -> None:
    await update_embedding_rows(
        table_name="canonical_keywords",
        rows=rows,
        embeddings=embeddings,
    )


async def _load_dump_rows(ids: list[int] | None = None) -> list[dict[str, object]]:
    return await load_all_rows(
        table_name="canonical_keywords",
        select_columns="id, code, display_name, embedding::text AS embedding_text, created_at",
        order_by="id ASC",
        ids=ids,
    )


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


def _format_timestamp(value: object) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _build_insert_statement(row: dict[str, object]) -> str:
    return (
        "INSERT INTO canonical_keywords "
        '(id, code, display_name, embedding, created_at) VALUES '
        f"({row['id']}, "
        f"'{_escape_sql_string(str(row['code']))}', "
        f"'{_escape_sql_string(str(row['display_name']))}', "
        f"'{row['embedding_text']}', "
        f"'{_format_timestamp(row['created_at'])}') "
        "ON CONFLICT (id) DO NOTHING;"
    )


def _build_filtered_batch_loader(
    rows: list[dict[str, object]],
) -> Callable[[int, int], Awaitable[list[dict[str, object]]]]:
    async def _load_filtered_rows(offset: int, limit: int) -> list[dict[str, object]]:
        return rows[offset : offset + limit]

    return _load_filtered_rows


async def main() -> None:
    args = _parse_args()
    _configure_stdout()

    resolver = build_canonical_keyword_resolver_service()
    await resolver.preload()

    async def _embed_rows(rows: list[dict[str, object]]) -> list[list[float]]:
        display_names = [str(row["display_name"]) for row in rows]
        return await resolver.embed_display_names(display_names)

    load_batch = _load_rows
    if args.ids:
        filtered_rows = await _load_dump_rows(args.ids)
        load_batch = _build_filtered_batch_loader(filtered_rows)

    await run_embedding_backfill(
        batch_size=BATCH_SIZE,
        load_batch=load_batch,
        embed_batch=_embed_rows,
        update_batch=_update_rows,
    )

    dump_rows = await _load_dump_rows(args.ids)
    for row in dump_rows:
        print(_build_insert_statement(row))

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
