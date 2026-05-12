from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy import text

from app.db.postgres import dispose_engine, get_session_factory
from app.services.canonical_keyword_resolver import (
    build_canonical_keyword_resolver_service,
)

BATCH_SIZE = 32


async def _load_rows(offset: int, limit: int) -> list[dict[str, object]]:
    query = text(
        """
        SELECT id, code, display_name, created_at
        FROM canonical_keywords
        ORDER BY id ASC
        OFFSET :offset
        LIMIT :limit
        """
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(query, {"offset": offset, "limit": limit})
        return [dict(row) for row in result.mappings().all()]


async def _update_rows(rows: list[dict[str, object]], embeddings: list[list[float]]) -> None:
    update_query = text(
        """
        UPDATE canonical_keywords
        SET embedding = CAST(:embedding AS vector)
        WHERE id = :id
        """
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        for row, embedding in zip(rows, embeddings, strict=True):
            vector_literal = "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"
            await session.execute(
                update_query,
                {
                    "id": row["id"],
                    "embedding": vector_literal,
                },
            )
        await session.commit()


async def _load_dump_rows() -> list[dict[str, object]]:
    query = text(
        """
        SELECT id, code, display_name, embedding::text AS embedding_text, created_at
        FROM canonical_keywords
        ORDER BY id ASC
        """
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(query)
        return [dict(row) for row in result.mappings().all()]


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
        f"'{_format_timestamp(row['created_at'])}');"
    )


async def main() -> None:
    resolver = build_canonical_keyword_resolver_service()
    await resolver.preload()

    offset = 0
    while True:
        rows = await _load_rows(offset, BATCH_SIZE)
        if not rows:
            break

        display_names = [str(row["display_name"]) for row in rows]
        embeddings = await resolver.embed_display_names(display_names)
        await _update_rows(rows, embeddings)
        offset += len(rows)

    dump_rows = await _load_dump_rows()
    for row in dump_rows:
        print(_build_insert_statement(row))

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
