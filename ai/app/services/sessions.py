import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis

from app.core.config import settings
from app.schemas.sessions import ProcessUtteranceRequest

CONTENTS_KEY_PREFIX = "contents"
STATUS_STARTED = "STARTED"
STATUS_TEXT_GENERATED = "TEXT_GENERATED"

_KOREAN_PARTICLES = (
    "은", "는", "이", "가", "을", "를", "에", "와", "과", "도", "만",
    "으로", "로", "에서", "께서", "이나", "나", "이라", "라",
)
_STOPWORDS = {"오늘", "우리", "가게", "저희", "정말", "너무", "많이", "조금"}


def _strip_particle(token: str) -> str:
    for particle in sorted(_KOREAN_PARTICLES, key=len, reverse=True):
        if token.endswith(particle) and len(token) > len(particle) + 1:
            return token[: -len(particle)]
    return token


def extract_keywords(utterance: str) -> list[str]:
    """규칙 기반 키워드 추출 placeholder.

    공백으로 토큰화 후 구두점 제거, 한국어 조사 제거, 불용어/길이 1 토큰 제거.
    중복은 입력 순서를 유지하며 제거.
    """
    cleaned = re.sub(r"[^\w\sㄱ-ㅎㅏ-ㅣ가-힣]", " ", utterance)
    seen: set[str] = set()
    keywords: list[str] = []
    for raw in cleaned.split():
        token = _strip_particle(raw.strip())
        if not token or len(token) < 2 or token in _STOPWORDS or token in seen:
            continue
        seen.add(token)
        keywords.append(token)
    return keywords


def build_draft_caption(
    keywords: list[str],
    owner_persona: str,
    weather_condition: str,
) -> tuple[str, list[str]]:
    """초안 caption + hashtags 생성 placeholder."""
    keyword_phrase = ", ".join(keywords) if keywords else "오늘의 풍경"
    caption = (
        f"{weather_condition} 오는 날, {owner_persona} 무드의 저희 가게에서 "
        f"{keyword_phrase}와 함께하는 시간 어떠세요?"
    )
    hashtags = [f"#{kw.replace(' ', '')}" for kw in keywords[:5]]
    if weather_condition:
        hashtags.append(f"#{weather_condition}오는날")
    return caption, hashtags


def build_guide_text(keywords: list[str]) -> str:
    """추출된 키워드를 모두 포함하는 촬영 안내문 생성."""
    if not keywords:
        return "촬영하실 때 가게의 분위기가 잘 드러나도록 예쁘게 찍어주세요!"
    keyword_phrase = ", ".join(keywords)
    return (
        f"{keyword_phrase}이(가) 모두 잘 보이도록 예쁘게 찍어주세요! "
        "촬영하실 때 아래 체크리스트를 꼭 확인해주세요."
    )


def session_key(session_id: str) -> str:
    return f"{CONTENTS_KEY_PREFIX}:{session_id}"


async def _replace_prefixed_fields(
    redis: Redis,
    key: str,
    prefix: str,
    values: list[str],
) -> None:
    existing_fields = await redis.hkeys(key)
    stale_fields = [field for field in existing_fields if field.startswith(prefix)]
    if stale_fields:
        await redis.hdel(key, *stale_fields)

    if values:
        mapping = {f"{prefix}{index}": value for index, value in enumerate(values, start=1)}
        await redis.hset(key, mapping=mapping)


async def upsert_content_session(
    redis: Redis,
    session_id: str,
    scalar_fields: dict[str, str],
    keywords: list[str] | None = None,
    drafts: list[str] | None = None,
    photos: list[str] | None = None,
) -> None:
    key = session_key(session_id)
    ttl = settings.SESSION_TTL_SECONDS
    expires_at = (datetime.now(UTC) + timedelta(seconds=ttl)).isoformat()

    mapping = {"status": STATUS_STARTED, **scalar_fields, "expires_at": expires_at}
    await redis.hset(key, mapping=mapping)

    if keywords is not None:
        await _replace_prefixed_fields(redis, key, "keyword:", keywords)
    if drafts is not None:
        await _replace_prefixed_fields(redis, key, "draft:", drafts)
    if photos is not None:
        await _replace_prefixed_fields(redis, key, "photo:", photos)

    await redis.expire(key, ttl)


@dataclass
class ProcessUtteranceResult:
    keywords: list[str]
    draft_caption: str
    draft_hashtags: list[str]
    guide_text: str


async def process_utterance(
    session_id: str,
    payload: ProcessUtteranceRequest,
    redis: Redis,
) -> ProcessUtteranceResult:
    keywords = extract_keywords(payload.utterance)
    draft_caption, draft_hashtags = build_draft_caption(
        keywords,
        owner_persona=payload.owner_persona,
        weather_condition=payload.weather.condition,
    )
    guide_text = build_guide_text(keywords)

    redis_payload = {
        "session_id": session_id,
        "store_id": str(payload.store_id),
        "status": STATUS_TEXT_GENERATED,
        "caption": draft_caption,
        "owner_persona": payload.owner_persona,
        "weather_condition": payload.weather.condition,
        "weather_temperature": str(payload.weather.temperature),
        "date": payload.date.isoformat(),
    }

    await upsert_content_session(
        redis,
        session_id,
        scalar_fields=redis_payload,
        keywords=keywords,
    )

    return ProcessUtteranceResult(
        keywords=keywords,
        draft_caption=draft_caption,
        draft_hashtags=draft_hashtags,
        guide_text=guide_text,
    )
