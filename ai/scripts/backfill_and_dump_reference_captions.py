from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Awaitable, Callable

from app.db.postgres import dispose_engine
from app.services.canonical_keyword_resolver import (
    build_canonical_keyword_resolver_service,
)
from scripts.backfill_utils import (
    load_all_rows,
    load_rows,
    run_embedding_backfill,
    update_embedding_rows,
)

BATCH_SIZE = 32


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill reference caption embeddings and dump INSERT SQL.",
    )
    parser.add_argument(
        "--ids",
        nargs="*",
        type=int,
        help="Optional reference caption ids to backfill and dump.",
    )
    return parser.parse_args()


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


async def _load_rows(offset: int, limit: int) -> list[dict[str, object]]:
    return await load_rows(
        table_name="reference_captions",
        select_columns="id, caption_content",
        order_by="id ASC",
        offset=offset,
        limit=limit,
    )


async def _update_rows(rows: list[dict[str, object]], embeddings: list[list[float]]) -> None:
    await update_embedding_rows(
        table_name="reference_captions",
        rows=rows,
        embeddings=embeddings,
    )


async def _load_dump_rows(ids: list[int] | None = None) -> list[dict[str, object]]:
    return await load_all_rows(
        table_name="reference_captions",
        select_columns="id, caption_content, embedding::text AS embedding_text",
        order_by="id ASC",
        ids=ids,
    )


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


def _build_insert_statement(row: dict[str, object]) -> str:
    return (
        "INSERT INTO reference_captions "
        "(id, caption_content, embedding) VALUES "
        f"({row['id']}, "
        f"'{_escape_sql_string(str(row['caption_content']))}', "
        f"'{row['embedding_text']}') "
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
        caption_texts = [str(row["caption_content"]) for row in rows]
        return await resolver.embed_passages(caption_texts)

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
