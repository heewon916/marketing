from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeAlias

from sqlalchemy import text

from app.db.postgres import get_session_factory

Row: TypeAlias = dict[str, object]
EmbedBatch: TypeAlias = Callable[[list[Row]], Awaitable[list[list[float]]]]


async def load_rows(
    *,
    table_name: str,
    select_columns: str,
    order_by: str,
    offset: int,
    limit: int,
) -> list[Row]:
    query = text(
        f"""
        SELECT {select_columns}
        FROM {table_name}
        ORDER BY {order_by}
        OFFSET :offset
        LIMIT :limit
        """
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(query, {"offset": offset, "limit": limit})
        return [dict(row) for row in result.mappings().all()]


async def load_all_rows(
    *,
    table_name: str,
    select_columns: str,
    order_by: str,
) -> list[Row]:
    query = text(
        f"""
        SELECT {select_columns}
        FROM {table_name}
        ORDER BY {order_by}
        """
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(query)
        return [dict(row) for row in result.mappings().all()]


def build_vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"


async def update_embedding_rows(
    *,
    table_name: str,
    rows: list[Row],
    embeddings: list[list[float]],
    id_column: str = "id",
    embedding_column: str = "embedding",
) -> None:
    update_query = text(
        f"""
        UPDATE {table_name}
        SET {embedding_column} = CAST(:embedding AS vector)
        WHERE {id_column} = :id
        """
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        for row, embedding in zip(rows, embeddings, strict=True):
            await session.execute(
                update_query,
                {
                    "id": row[id_column],
                    "embedding": build_vector_literal(embedding),
                },
            )
        await session.commit()


async def run_embedding_backfill(
    *,
    batch_size: int,
    load_batch: Callable[[int, int], Awaitable[list[Row]]],
    embed_batch: EmbedBatch,
    update_batch: Callable[[list[Row], list[list[float]]], Awaitable[None]],
) -> None:
    offset = 0
    while True:
        rows = await load_batch(offset, batch_size)
        if not rows:
            break
        embeddings = await embed_batch(rows)
        await update_batch(rows, embeddings)
        offset += len(rows)
