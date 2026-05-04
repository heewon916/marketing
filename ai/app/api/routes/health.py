from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="헬스 체크")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
