import argparse
import json
import time

import httpx

from app.services.caption_generation import CaptionGenerationRequest
from app.services.caption_generation import build_caption_generation_service


def run_probe(timeout_seconds: float) -> dict:
    service = build_caption_generation_service()
    result: dict[str, object] = {
        "base_url": service.base_url,
        "service_timeout_seconds": service.timeout_seconds,
        "probe_timeout_seconds": timeout_seconds,
        "max_tokens": service.max_tokens,
    }

    request = CaptionGenerationRequest(
        keywords=["동절기 메뉴"],
        owner_persona="aesthetic",
        utterance="마늘 치킨 메뉴 홍보 문구 부탁해요",
        weather_tags=["PRECIP_CLEAR", "TEMP_MILD"],
        reference_captions=[],
        menu_candidates=[],
    )
    prompt = service._pipeline.build_prompt(request)
    full_payload = service._build_request_payload(
        prompt,
        include_response_format=True,
        strict_language=False,
    )
    result["full_prompt_chars"] = len(prompt)
    result["full_payload_chars"] = len(json.dumps(full_payload, ensure_ascii=False))

    minimal_payload = {
        "messages": [
            {
                "role": "system",
                "content": "guide_text와 caption만 있는 JSON 객체 하나만 반환하세요.",
            },
            {
                "role": "user",
                "content": (
                    'JSON 객체 하나로만 답하세요. {"guide_text":"...",'
                    '"caption":"..."} 메뉴 홍보용 한국어 문장 2개를 짧게 '
                    "작성하세요. 키워드: 마늘 치킨"
                ),
            },
        ],
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 120,
    }

    schema = {
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {
                "guide_text": {"type": "string"},
                "caption": {"type": "string"},
            },
            "required": ["guide_text", "caption"],
        },
    }

    headers = service._build_request_headers()

    start = time.perf_counter()
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(service._health_url)
        result["health_status"] = response.status_code
        result["health_elapsed_ms"] = int((time.perf_counter() - start) * 1000)
    except Exception as exc:  # pragma: no cover - diagnostic script
        result["health_error"] = repr(exc)

    probe_cases = {
        "full_request": full_payload,
        "minimal_no_schema": minimal_payload,
        "minimal_with_schema": {**minimal_payload, "response_format": schema},
    }

    for name, payload in probe_cases.items():
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(
                    service._chat_url,
                    headers=headers,
                    json=payload,
                )
            result[f"{name}_status"] = response.status_code
            result[f"{name}_elapsed_ms"] = int((time.perf_counter() - start) * 1000)
            result[f"{name}_preview"] = response.text[:300]
        except Exception as exc:  # pragma: no cover - diagnostic script
            result[f"{name}_error"] = repr(exc)
            result[f"{name}_elapsed_ms"] = int((time.perf_counter() - start) * 1000)

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=65.0)
    args = parser.parse_args()
    print(json.dumps(run_probe(args.timeout), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
