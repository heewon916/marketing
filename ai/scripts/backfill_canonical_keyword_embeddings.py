from __future__ import annotations

import asyncio

from app.db.postgres import dispose_engine
from scripts.backfill_utils import (
    load_rows,
    run_embedding_backfill,
    update_embedding_rows,
)
from app.services.canonical_keyword_resolver import (
    build_canonical_keyword_resolver_service,
)

BATCH_SIZE = 32


async def _load_rows(offset: int, limit: int) -> list[dict[str, object]]:
    return await load_rows(
        table_name="canonical_keywords",
        select_columns="id, display_name",
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


async def main() -> None:
    resolver = build_canonical_keyword_resolver_service()
    await resolver.preload()

    async def _embed_rows(rows: list[dict[str, object]]) -> list[list[float]]:
        display_names = [str(row["display_name"]) for row in rows]
        return await resolver.embed_display_names(display_names)

    await run_embedding_backfill(
        batch_size=BATCH_SIZE,
        load_batch=_load_rows,
        embed_batch=_embed_rows,
        update_batch=_update_rows,
    )

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
