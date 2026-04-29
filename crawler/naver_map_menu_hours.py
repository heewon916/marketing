"""Standalone Naver Map crawler for business hours and menu data.

Install:
    pip install playwright
    playwright install chromium

Run:
    python naver_map_menu_hours.py --name "카페A" --name "카페B"
    python naver_map_menu_hours.py --name "카페A" --output result.json
    python naver_map_menu_hours.py --name "카페A" --headful --timeout-sec 30
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import urllib.parse
from collections import defaultdict, deque
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
from fastapi import FastAPI, HTTPException, Query

import sys
import asyncio

# 윈도우 환경에서 Playwright (Subprocess) 실행 시 발생하는 NotImplementedError 방지
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page, Playwright


logger = logging.getLogger("naver_map_menu_hours")

app = FastAPI(title="Naver Map Crawler API")

NAVER_MAP_BASE_URL = "https://map.naver.com/p/search/"
TAB_CONFIG = {
    "home": "home",
    "menu": "menu",
    "information": "information",
}
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]
_VIEWPORT_POOL = [
    {"width": 1400, "height": 900},
    {"width": 1280, "height": 800},
    {"width": 1440, "height": 900},
]
BLOCK_HOSTS = frozenset(
    {
        "mc.naver.com",
        "beagle.naver.com",
        "collect.veta.naver.com",
        "wcs.naver.com",
        "api.vworld.kr",
    }
)
ALLOWED_IMAGE_HOSTS = frozenset(
    {
        "pup-review-phinf.pstatic.net",
        "ldb-phinf.pstatic.net",
    }
)
_BLOCK_SEARCH = frozenset({"image", "font", "media", "stylesheet", "websocket", "other"})
_BLOCK_TAB = frozenset({"font", "media", "websocket", "other"})
NAV_TABS = {"홈", "메뉴", "리뷰", "사진", "정보"}
LABEL_TOKENS = {
    "대표",
    "best",
    "new",
    "인기",
    "추천",
    "시그니처",
    "준비중",
    "best seller",
    "사진",
}
_LABEL_TOKEN_CASEFOLDS = frozenset(token.casefold() for token in LABEL_TOKENS)
MENU_STOP_PHRASES = ("메뉴 음식명과 가격", "메뉴판 이미지로 보기", "이용안내")
PRICE_RE = re.compile(r"^[\d,]+(?:원)?$")
PLACE_URL_RE = re.compile(r"(https://pcmap\.place\.naver\.com/[a-z]+/\d+)")
PLACE_CATEGORY_SPLIT_RE = re.compile(r"\s*(?:,|/|\||\u00b7)\s*")
DAY_FIELD_MAP = {
    "월": "mon_hours",
    "화": "tues_hours",
    "수": "wed_hours",
    "목": "thur_hours",
    "금": "fri_hours",
    "토": "sat_hours",
    "일": "sun_hours",
}
DAY_ORDER = ["월", "화", "수", "목", "금", "토", "일"]
DAY_FIELDS = [DAY_FIELD_MAP[day] for day in DAY_ORDER]
TAB_SCROLL_STEPS = {"home": 0, "menu": 2, "information": 0}
TAB_READY_SELECTORS = {
    "home": ("body",),
    "menu": ("li", "img[src]", "body"),
    "information": ("body",),
}
SETTLE_WAIT_SECONDS = 0.5
SCROLL_WAIT_SECONDS = 0.35
SCROLL_STEP_PX = 800
SEARCH_RESPONSE_TIMEOUT_SECONDS = 8
SEARCH_FRAME_TIMEOUT_SECONDS = 10
SEARCH_URL_EXTRACTION_POLL_SECONDS = 0.5
MAX_STALE_SCROLL_ROUNDS = 2


class CrawlerSetupError(RuntimeError):
    """Raised when the local crawler runtime is unavailable."""


class PlaceNotFoundError(RuntimeError):
    """Raised when a place could not be resolved from a query."""


@dataclass(frozen=True)
class MenuCardPayload:
    menu_name: str
    price: int | None = None
    menu_description: str | None = None
    image_url: str | None = None


def configure_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def random_ua() -> str:
    return random.choice(_UA_POOL)


def read_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def skip_nav_header(lines: list[str]) -> int:
    found: set[str] = set()
    for index, line in enumerate(lines):
        if line in NAV_TABS:
            found.add(line)
            if found == NAV_TABS:
                return index + 1
    return 0


def normalize_compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_optional_text(value: Any) -> str | None:
    text = normalize_compact_text(value)
    return text or None


def empty_business_hours() -> dict[str, str | None]:
    return {field: None for field in DAY_FIELDS}


def parse_menu_text(menu_text: str) -> list[dict[str, Any]]:
    lines = read_lines(menu_text)
    body = lines[skip_nav_header(lines) :]
    menus: list[dict[str, Any]] = []
    pending_name: str | None = None
    pending_desc: str | None = None

    for index, line in enumerate(body):
        if any(line.startswith(stop) for stop in MENU_STOP_PHRASES):
            break
        if line.lower() in _LABEL_TOKEN_CASEFOLDS:
            continue
        if PRICE_RE.fullmatch(line):
            price = int(line.replace("원", "").replace(",", ""))
            if pending_name:
                menus.append(
                    {
                        "menu_name": pending_name,
                        "price": price,
                        "menu_description": pending_desc,
                    }
                )
                pending_name = None
                pending_desc = None
            continue
        if len(line) <= 30:
            next_line = body[index + 1] if index + 1 < len(body) else ""
            if pending_name and pending_desc is None and PRICE_RE.fullmatch(next_line):
                pending_desc = line
                continue
            if pending_name:
                menus.append(
                    {
                        "menu_name": pending_name,
                        "price": None,
                        "menu_description": pending_desc,
                    }
                )
            pending_name = line
            pending_desc = None
            continue
        pending_desc = line

    if pending_name:
        menus.append(
            {
                "menu_name": pending_name,
                "price": None,
                "menu_description": pending_desc,
            }
        )

    return menus


def normalize_hours_value(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    return value.replace(" ~ ", " - ").replace(" ~", " - ").replace("~ ", " - ")


def expand_day_expression(expr: str) -> list[str]:
    expr = expr.replace("요일", "").replace("매주", "").replace(" ", "")
    if not expr:
        return []
    if "," in expr:
        fields: list[str] = []
        for part in expr.split(","):
            fields.extend(expand_day_expression(part))
        return list(dict.fromkeys(fields))

    range_match = re.fullmatch(r"([월화수목금토일])[~-]([월화수목금토일])", expr)
    if range_match:
        start_idx = DAY_ORDER.index(range_match.group(1))
        end_idx = DAY_ORDER.index(range_match.group(2))
        if start_idx <= end_idx:
            return [DAY_FIELD_MAP[day] for day in DAY_ORDER[start_idx : end_idx + 1]]
        return [DAY_FIELD_MAP[day] for day in DAY_ORDER[start_idx:] + DAY_ORDER[: end_idx + 1]]

    return [DAY_FIELD_MAP[expr]] if expr in DAY_FIELD_MAP else []


def split_hour_segments(lines: list[str]) -> list[str]:
    segments: list[str] = []
    current_day_prefix = None
    for raw_line in lines:
        line = re.sub(r"\s+", " ", raw_line.strip())
        if not line or line in NAV_TABS:
            continue
        for part in re.split(r"\s*/\s*", line):
            segment = part.strip()
            if not segment:
                continue
            if segment.startswith("영업시간"):
                segment = segment.replace("영업시간", "", 1).strip()
            if segment.startswith("오늘") or segment.startswith("접기") or segment.startswith("더보기"):
                continue
            
            if re.fullmatch(r"매일|평일|주말|[월화수목금토일](요일)?", segment):
                current_day_prefix = segment
                continue
            
            if current_day_prefix and (re.search(r"\d{1,2}:\d{2}", segment) or "휴무" in segment):
                segment = f"{current_day_prefix} {segment}"
                current_day_prefix = None

            if segment.startswith("라스트오더") or segment.startswith("브레이크타임") or segment.startswith("휴게시간"):
                continue
            if re.match(r"^(매일|평일|주말)\b", segment) and (
                re.search(r"\d{1,2}:\d{2}", segment) or "휴무" in segment
            ):
                segments.append(segment)
                continue
            if re.match(
                r"^(매주\s*)?([월화수목금토일](요일)?)(\s*[~,/-]\s*[월화수목금토일](요일)?)?",
                segment,
            ) and (re.search(r"\d{1,2}:\d{2}", segment) or "휴무" in segment):
                segments.append(segment)
    return segments


def parse_business_hours_from_segments(segments: list[str]) -> dict[str, str | None]:
    result = empty_business_hours()
    general_all: str | None = None
    weekdays: str | None = None
    weekends: str | None = None
    specifics: dict[str, str] = {}

    for segment in segments:
        clean = normalize_hours_value(segment).replace("매주 ", "")
        general_match = re.match(r"^(매일|평일|주말)\s+(.+)$", clean)
        if general_match:
            head, value = general_match.groups()
            if head == "매일":
                general_all = value
            elif head == "평일":
                weekdays = value
            else:
                weekends = value
            continue

        specific_match = re.match(
            r"^([월화수목금토일](?:요일)?(?:\s*[~,/-]\s*[월화수목금토일](?:요일)?)?(?:\s*,\s*[월화수목금토일](?:요일)?)*)\s+(.+)$",
            clean,
        )
        if not specific_match:
            continue
        expr, value = specific_match.groups()
        for field in expand_day_expression(expr):
            specifics[field] = value

    if general_all:
        for field in DAY_FIELDS:
            result[field] = general_all
    if weekdays:
        for day in DAY_ORDER[:5]:
            result[DAY_FIELD_MAP[day]] = weekdays
    if weekends:
        for day in DAY_ORDER[5:]:
            result[DAY_FIELD_MAP[day]] = weekends
    for field, value in specifics.items():
        result[field] = value
    return result


def parse_business_hours(home_text: str, info_text: str = "") -> dict[str, str | None]:
    return parse_business_hours_from_segments(split_hour_segments(read_lines(home_text) + read_lines(info_text)))


def normalize_business_hours_day_labels(value: Any) -> list[str]:
    normalized = normalize_optional_text(value)
    if normalized is None:
        return []
    compact = normalized.replace("요일", "").replace("매주", "").replace(" ", "")
    if compact == "매일":
        return DAY_FIELDS
    if compact == "평일":
        return [DAY_FIELD_MAP[day] for day in DAY_ORDER[:5]]
    if compact == "주말":
        return [DAY_FIELD_MAP[day] for day in DAY_ORDER[5:]]
    if compact in DAY_FIELD_MAP:
        return [DAY_FIELD_MAP[compact]]
    return expand_day_expression(compact)


def build_structured_business_hours(raw_rows: Any) -> dict[str, str | None]:
    business_hours = empty_business_hours()
    if not isinstance(raw_rows, list):
        return business_hours

    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            continue
        fields = normalize_business_hours_day_labels(raw_row.get("day"))
        value = normalize_optional_text(raw_row.get("time"))
        if not fields or value is None:
            continue
        for field in fields:
            business_hours[field] = value
    return business_hours


def has_any_business_hours_value(business_hours: dict[str, str | None] | None) -> bool:
    return bool(business_hours) and any(value is not None for value in business_hours.values())


def normalize_menu_name_key(value: Any) -> str:
    return normalize_compact_text(value).casefold()


def parse_menu_price_value(value: Any) -> int | None:
    text = normalize_compact_text(value).replace(" ", "").replace(",", "").replace("원", "")
    if not text.isdigit():
        return None
    return int(text)


def is_allowed_image_url(url: str) -> bool:
    host = urllib.parse.urlparse(url).hostname or ""
    return host.lower() in ALLOWED_IMAGE_HOSTS


def normalize_image_source_url(url: Any) -> str | None:
    normalized = normalize_optional_text(url)
    if normalized is None:
        return None

    parsed = urllib.parse.urlparse(normalized)
    if (parsed.hostname or "").lower() == "search.pstatic.net":
        source_values = urllib.parse.parse_qs(parsed.query).get("src")
        if source_values:
            decoded_source = normalize_optional_text(source_values[0])
            if decoded_source:
                normalized = decoded_source

    if not is_allowed_image_url(normalized):
        return None

    high_quality = re.sub(r"/thumbnail/\d+x\d+(?:crop)?/", "/", normalized)
    return high_quality.split("?")[0]


def normalize_menu_card_payloads(raw_payloads: list[dict[str, Any]]) -> list[MenuCardPayload]:
    normalized_payloads: list[MenuCardPayload] = []
    seen: set[tuple[str, int | None, str | None, str | None]] = set()

    for raw_payload in raw_payloads:
        if not isinstance(raw_payload, dict):
            continue

        menu_name = normalize_optional_text(raw_payload.get("menu_name"))
        if menu_name is None or menu_name.casefold() in _LABEL_TOKEN_CASEFOLDS:
            continue

        payload = MenuCardPayload(
            menu_name=menu_name,
            price=parse_menu_price_value(raw_payload.get("price_text") or raw_payload.get("price")),
            menu_description=normalize_optional_text(raw_payload.get("menu_description")),
            image_url=normalize_image_source_url(raw_payload.get("image_url")),
        )
        signature = (
            normalize_menu_name_key(payload.menu_name),
            payload.price,
            payload.menu_description,
            payload.image_url,
        )
        if signature in seen:
            continue
        seen.add(signature)
        normalized_payloads.append(payload)

    return normalized_payloads


def build_menus_with_candidates(menu_text: str, menu_cards: list[MenuCardPayload]) -> list[dict[str, Any]]:
    parsed_menus = parse_menu_text(menu_text)
    if not parsed_menus:
        return [
            {
                "menu_name": menu_card.menu_name,
                "price": menu_card.price,
                "menu_description": menu_card.menu_description,
            }
            for menu_card in menu_cards
        ]

    menu_card_queues: defaultdict[str, deque[MenuCardPayload]] = defaultdict(deque)
    for menu_card in menu_cards:
        name_key = normalize_menu_name_key(menu_card.menu_name)
        if name_key:
            menu_card_queues[name_key].append(menu_card)

    menus: list[dict[str, Any]] = []
    for parsed_menu in parsed_menus:
        name_key = normalize_menu_name_key(parsed_menu["menu_name"])
        matched_card = menu_card_queues[name_key].popleft() if name_key and menu_card_queues[name_key] else None
        menus.append(
            {
                "menu_name": parsed_menu["menu_name"],
                "price": (
                    parsed_menu["price"]
                    if parsed_menu["price"] is not None
                    else matched_card.price if matched_card else None
                ),
                "menu_description": (
                    parsed_menu["menu_description"]
                    if parsed_menu["menu_description"] is not None
                    else matched_card.menu_description if matched_card else None
                ),
            }
        )

    return menus




async def configure_page(page: Page, *, search_mode: bool) -> None:
    block_types = _BLOCK_SEARCH if search_mode else _BLOCK_TAB

    async def handle(route) -> None:
        request = route.request
        if any(host in request.url for host in BLOCK_HOSTS) or request.resource_type in block_types:
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", handle)


async def wait_for_page_ready(page: Page, *, ready_selectors: tuple[str, ...]) -> None:
    for selector in ready_selectors:
        try:
            await page.locator(selector).first.wait_for(state="attached", timeout=1500)
            break
        except Exception:
            continue

    with suppress(Exception):
        await page.wait_for_load_state("networkidle", timeout=int(SETTLE_WAIT_SECONDS * 1000))
    await asyncio.sleep(SETTLE_WAIT_SECONDS)


async def scroll_page(page: Page, *, max_rounds: int) -> None:
    stale_rounds = 0
    for _ in range(max_rounds):
        before = await page.evaluate("() => ({ top: window.scrollY, height: document.body.scrollHeight })")
        await page.evaluate(f"window.scrollBy(0, {SCROLL_STEP_PX})")
        with suppress(Exception):
            await page.wait_for_load_state("networkidle", timeout=int(SCROLL_WAIT_SECONDS * 1000))
        await asyncio.sleep(SCROLL_WAIT_SECONDS)
        after = await page.evaluate("() => ({ top: window.scrollY, height: document.body.scrollHeight })")
        if after["top"] <= before["top"] and after["height"] == before["height"]:
            stale_rounds += 1
            if stale_rounds >= MAX_STALE_SCROLL_ROUNDS:
                break
        else:
            stale_rounds = 0


async def fetch_tab_text(
    page: Page,
    tab_url: str,
    *,
    timeout_ms: int,
    scroll_steps: int = 0,
    ready_selectors: tuple[str, ...] = ("body",),
) -> str:
    await page.goto(tab_url, wait_until="domcontentloaded", timeout=timeout_ms)
    await wait_for_page_ready(page, ready_selectors=ready_selectors)
    await scroll_page(page, max_rounds=scroll_steps)
    return (await page.evaluate("() => document.body.innerText")).strip()


async def extract_structured_business_hours(page: Page) -> dict[str, str | None]:
    raw_rows = await page.evaluate(
        """
        () => {
            const normalize = (value) => (value || '').replace(/\s+/g, ' ').trim();
            const sectionRoots = Array.from(
                document.querySelectorAll('.PIbes .O8qbU.pSavy, #app-root .place_section_content .O8qbU.pSavy')
            );
            const section = sectionRoots.find((root) => {
                const text = normalize(root.textContent || '');
                return (
                    text.includes('\\uc601\\uc5c5\\uc2dc\\uac04') ||
                    text.includes('\\uc601\\uc5c5 \\uc911') ||
                    text.includes('\\ud3bc\\uccd0\\ubcf4\\uae30')
                );
            });
            if (!section) {
                return [];
            }

            const pickText = (row, selectors) => {
                for (const selector of selectors) {
                    const text = normalize(row.querySelector(selector)?.textContent || '');
                    if (text) {
                        return text;
                    }
                }
                return '';
            };

            return Array.from(section.querySelectorAll('.w9QyJ')).map((row) => ({
                day: pickText(row, ['.A_cdD .i8cJw', '.i8cJw']),
                time: pickText(row, ['.A_cdD .H3ua4', '.H3ua4']),
                text: normalize(row.textContent || ''),
            }));
        }
        """
    )
    return build_structured_business_hours(raw_rows)


async def expand_business_hours_section(page: Page) -> bool:
    expanded = bool(
        await page.evaluate(
            """
            () => {
                const normalize = (value) => (value || '').replace(/\s+/g, ' ').trim();
                const sectionRoots = Array.from(
                    document.querySelectorAll('.PIbes .O8qbU.pSavy, #app-root .place_section_content .O8qbU.pSavy')
                );
                const section = sectionRoots.find((root) => {
                    const text = normalize(root.textContent || '');
                    return (
                        text.includes('\\uc601\\uc5c5\\uc2dc\\uac04') ||
                        text.includes('\\uc601\\uc5c5 \\uc911') ||
                        text.includes('\\ud3bc\\uccd0\\ubcf4\\uae30')
                    );
                });
                if (!section) {
                    return false;
                }

                const candidates = Array.from(
                    section.querySelectorAll('a[role="button"], button[role="button"], a, button, [aria-expanded], [aria-expander]')
                );
                for (const candidate of candidates) {
                    const text = normalize(candidate.textContent || '');
                    const ariaExpanded = candidate.getAttribute('aria-expanded');
                    const ariaExpander = candidate.getAttribute('aria-expander');
                    if (
                        text.includes('\\ud3bc\\uccd0\\ubcf4\\uae30') ||
                        ariaExpanded === 'false' ||
                        ariaExpander === 'true'
                    ) {
                        candidate.click();
                        return true;
                    }
                }
                return false;
            }
            """
        )
    )
    if expanded:
        with suppress(Exception):
            await page.wait_for_load_state("networkidle", timeout=int(SETTLE_WAIT_SECONDS * 1000))
        await asyncio.sleep(SETTLE_WAIT_SECONDS)
    return expanded


async def fetch_home_tab_data(page: Page, tab_url: str, *, timeout_ms: int) -> tuple[str, dict[str, str | None]]:
    await page.goto(tab_url, wait_until="domcontentloaded", timeout=timeout_ms)
    await wait_for_page_ready(page, ready_selectors=TAB_READY_SELECTORS["home"])
    await scroll_page(page, max_rounds=TAB_SCROLL_STEPS["home"])

    home_text = (await page.evaluate("() => document.body.innerText")).strip()
    structured_business_hours = await extract_structured_business_hours(page)
    if not has_any_business_hours_value(structured_business_hours) and await expand_business_hours_section(page):
        home_text = (await page.evaluate("() => document.body.innerText")).strip()
        structured_business_hours = await extract_structured_business_hours(page)

    return home_text, structured_business_hours


async def extract_menu_card_payloads(page: Page) -> list[MenuCardPayload]:
    raw_payloads = await page.evaluate(
        """
        (labelTokens) => {
            const normalize = (value) => (value || '').replace(/\s+/g, ' ').trim();
            const isVisible = (element) => {
                if (!(element instanceof Element)) {
                    return false;
                }
                const style = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();
                return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
            };
            const isPriceLine = (line) => /^[\\d,]+\\s*(?:\\uC6D0)?$/.test(line);
            const isLabel = (line) => labelTokens.includes(line.toLowerCase());
            const payloads = [];
            const structuredCards = Array.from(document.querySelectorAll('li.E2jtL'));
            for (const card of structuredCards) {
                if (!isVisible(card)) {
                    continue;
                }

                const menuName = normalize(card.querySelector('.lPzHi')?.textContent || '');
                const priceText = normalize(card.querySelector('.p2H02')?.textContent || '');
                const menuDescription = normalize(card.querySelector('.okI98')?.textContent || '') || null;
                const imageNode = card.querySelector('.place_thumb img[src]');
                if (!menuName || isLabel(menuName) || (!priceText && !imageNode)) {
                    continue;
                }

                payloads.push({
                    menu_name: menuName,
                    menu_description: menuDescription,
                    price_text: priceText || null,
                    image_url: normalize(imageNode?.currentSrc || imageNode?.src || '') || null,
                });
            }

            if (payloads.length === 0) {
                const elements = Array.from(document.querySelectorAll('li, article, section, div'));
                for (const element of elements) {
                    if (!isVisible(element)) {
                        continue;
                    }

                    const rawText = normalize(element.innerText || '');
                    if (!rawText || rawText.length > 160) {
                        continue;
                    }

                    const lines = rawText
                        .split('\\n')
                        .map(normalize)
                        .filter(Boolean);
                    if (lines.length === 0 || lines.length > 8) {
                        continue;
                    }

                    const imageNode = element.querySelector('img[src]');
                    const hasPrice = lines.some(isPriceLine);
                    if (!imageNode && !hasPrice) {
                        continue;
                    }

                    const candidateLines = lines.filter((line) => !isLabel(line));
                    if (candidateLines.length === 0) {
                        continue;
                    }

                    let menuName = null;
                    let menuDescription = null;
                    let priceText = null;

                    for (const line of candidateLines) {
                        if (isPriceLine(line)) {
                            priceText = priceText || line;
                            continue;
                        }
                        if (!menuName) {
                            menuName = line;
                            continue;
                        }
                        if (!menuDescription) {
                            menuDescription = line;
                        }
                    }

                    if (!menuName) {
                        continue;
                    }

                    payloads.push({
                        menu_name: menuName,
                        menu_description: menuDescription,
                        price_text: priceText,
                        image_url: normalize(imageNode?.currentSrc || imageNode?.src || '') || null,
                    });
                }
            }

            return payloads;
        }
        """,
        sorted(_LABEL_TOKEN_CASEFOLDS),
    )
    return normalize_menu_card_payloads(raw_payloads)


async def fetch_menu_tab_data(page: Page, tab_url: str, *, timeout_ms: int) -> tuple[str, list[MenuCardPayload]]:
    await page.goto(tab_url, wait_until="domcontentloaded", timeout=timeout_ms)
    await wait_for_page_ready(page, ready_selectors=TAB_READY_SELECTORS["menu"])
    await scroll_page(page, max_rounds=TAB_SCROLL_STEPS["menu"])
    menu_text = (await page.evaluate("() => document.body.innerText")).strip()
    menu_cards = await extract_menu_card_payloads(page)
    return menu_text, menu_cards


@app.get("/api/search")
async def search_places(keyword: str = Query(..., min_length=1)):
    from playwright.async_api import async_playwright
    import asyncio
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                viewport=random.choice(_VIEWPORT_POOL),
                user_agent=random_ua(),
                locale="ko-KR",
            )
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = await context.new_page()
            await configure_page(page, search_mode=True)
            
            search_data = None
            async def handle_response(response):
                nonlocal search_data
                if "api/search/allSearch" in response.url:
                    try:
                        search_data = await response.json()
                    except Exception:
                        pass

            page.on("response", handle_response)
            
            search_url = NAVER_MAP_BASE_URL + urllib.parse.quote(keyword)
            
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=15000)
            except Exception:
                pass # Timeout is fine if we already got the data
                
            for _ in range(10):
                if search_data:
                    break
                await asyncio.sleep(0.5)
                
            results = []
            if search_data:
                try:
                    places = search_data.get("result", {}).get("place", {}).get("list", [])
                    if not places:
                        # Fallback for some searches that might return empty list but have data elsewhere
                        pass
                    for p in places[:10]:
                        if not isinstance(p, dict):
                            continue
                        place_id = p.get("id")
                        name = p.get("name")
                        address = p.get("address")
                        if place_id and name:
                            results.append({
                                "name": name,
                                "address": address or "",
                                "place_id": str(place_id)
                            })
                except Exception as e:
                    logger.warning(f"Error parsing JSON data: {e}")
            
            await browser.close()
            return {"status": "success", "data": results}
    except Exception as e:
        logger.exception("Search API error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/place/{place_id}")
async def get_place_detail(place_id: str):
    from playwright.async_api import async_playwright
    import asyncio
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                viewport=random.choice(_VIEWPORT_POOL),
                user_agent=random_ua(),
                locale="ko-KR",
            )
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = await context.new_page()
            await configure_page(page, search_mode=False)
            
            place_url = f"https://pcmap.place.naver.com/restaurant/{place_id}"
            
            timeout_ms = 15000
            home_text, structured_business_hours = await fetch_home_tab_data(
                page,
                f"{place_url}/{TAB_CONFIG['home']}",
                timeout_ms=timeout_ms,
            )
            await asyncio.sleep(random.uniform(0.4, 0.8))
            menu_text, menu_cards = await fetch_menu_tab_data(
                page,
                f"{place_url}/{TAB_CONFIG['menu']}",
                timeout_ms=timeout_ms,
            )
            await asyncio.sleep(random.uniform(0.4, 0.8))
            info_text = await fetch_tab_text(
                page,
                f"{place_url}/{TAB_CONFIG['information']}",
                timeout_ms=timeout_ms,
                scroll_steps=TAB_SCROLL_STEPS["information"],
                ready_selectors=TAB_READY_SELECTORS["information"],
            )
            
            business_hours = (
                structured_business_hours
                if has_any_business_hours_value(structured_business_hours)
                else parse_business_hours(home_text, info_text)
            )
            menus = build_menus_with_candidates(menu_text, menu_cards)
            
            await browser.close()
            
            return {
                "status": "success", 
                "data": {
                    "place_id": place_id,
                    "business_hours": business_hours,
                    "menus": menus
                }
            }
    except Exception as e:
        logger.exception(f"Detail API error for {place_id}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    configure_logging("INFO")
    uvicorn.run("naver_map_menu_hours:app", host="0.0.0.0", port=8000)
