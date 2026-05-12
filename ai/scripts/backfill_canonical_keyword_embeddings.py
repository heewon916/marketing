from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.postgres import dispose_engine, get_session_factory
from app.services.canonical_keyword_resolver import (
    build_canonical_keyword_resolver_service,
)

BATCH_SIZE = 32


async def _load_rows(offset: int, limit: int) -> list[dict[str, object]]:
    query = text(
        """
        SELECT id, display_name
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

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
