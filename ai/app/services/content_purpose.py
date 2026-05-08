from __future__ import annotations

from typing import Literal

ALLOWED_CONTENT_PURPOSES = (
    "메뉴 홍보",
    "영업 공지",
    "일상 공유",
)

ContentPurpose = Literal["메뉴 홍보", "영업 공지", "일상 공유"]
