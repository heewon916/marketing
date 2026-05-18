"""
레퍼런스 이미지 톤 프로파일 추출기

사용법:
  python tone_profiler.py <이미지_폴더_경로>


예시:
  python tone_profiler.py C:/Users/SSAFY/Downloads/reference_feed

출력:
  1. 개별 이미지 분석 결과
  2. 전체 레퍼런스의 평균/표준편차 → "목표 톤 프로파일"
  3. 베이스 프리셋 JSON (에이전트에 바로 적용 가능)
  4. 히스토그램 시각화 PNG
"""

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import cv2
import numpy as np


@dataclass
class ToneProfile:
    """단일 이미지의 톤 프로파일"""
    filename: str

    # ── 밝기/콘트라스트 (LAB L채널, 0-255) ──
    brightness_mean: float       # 평균 밝기. 낮을수록 어두움.
    brightness_std: float        # 콘트라스트. 높을수록 명암 차이 큼.
    black_point: float           # 하위 5% 밝기값. 0이면 순수 검정, 높으면 리프트드 블랙.
    white_point: float           # 상위 95% 밝기값. 255면 순백, 낮으면 하이라이트 억제.

    # ── 색온도/색조 (LAB a,b채널) ──
    temperature: float           # b채널 평균. 양수=따뜻(노랑), 음수=차가움(파랑).
    tint: float                  # a채널 평균. 양수=붉은, 음수=초록.

    # ── 채도 (HSV S채널, 0-255) ──
    saturation_mean: float       # 평균 채도. 낮을수록 뮤트.
    saturation_std: float        # 채도 분산. 높으면 채도 편차 큼.

    # ── 지배 색상 (HSV H채널, 0-179) ──
    dominant_hue: float          # 가장 많이 등장하는 색상 (0=빨강, 15=주황, 30=노랑, ...)
    hue_concentration: float     # 지배 색상 비율 (0-1). 높을수록 색상 통일.


def analyze_image(img_path: str) -> ToneProfile | None:
    """단일 이미지의 톤 프로파일 추출"""
    img = cv2.imread(img_path)
    if img is None:
        print(f"  [SKIP] 읽기 실패: {img_path}")
        return None

    # 리사이즈 (분석 속도 + 노이즈 평균화)
    h, w = img.shape[:2]
    if max(h, w) > 1024:
        scale = 1024 / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    # ── LAB 색공간 분석 ──
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_ch = lab[:, :, 0].astype(np.float64)
    a_ch = lab[:, :, 1].astype(np.float64) - 128  # 중심을 0으로
    b_ch = lab[:, :, 2].astype(np.float64) - 128

    brightness_mean = float(np.mean(l_ch))
    brightness_std = float(np.std(l_ch))
    black_point = float(np.percentile(l_ch, 5))
    white_point = float(np.percentile(l_ch, 95))

    temperature = float(np.mean(b_ch))  # 양수=따뜻
    tint = float(np.mean(a_ch))         # 양수=붉은

    # ── HSV 채도/색상 분석 ──
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    s_ch = hsv[:, :, 1].astype(np.float64)
    h_ch = hsv[:, :, 0].astype(np.float64)

    saturation_mean = float(np.mean(s_ch))
    saturation_std = float(np.std(s_ch))

    # 지배 색상: 채도가 30 이상인 픽셀만 대상 (무채색 제외)
    chromatic_mask = hsv[:, :, 1] > 30
    if np.sum(chromatic_mask) > 100:
        h_chromatic = h_ch[chromatic_mask]
        hist, bins = np.histogram(h_chromatic, bins=36, range=(0, 180))
        dominant_bin = int(np.argmax(hist))
        dominant_hue = float(dominant_bin * 5 + 2.5)  # 빈 중앙값
        hue_concentration = float(hist[dominant_bin] / np.sum(hist))
    else:
        dominant_hue = 0.0
        hue_concentration = 0.0

    return ToneProfile(
        filename=Path(img_path).name,
        brightness_mean=round(brightness_mean, 1),
        brightness_std=round(brightness_std, 1),
        black_point=round(black_point, 1),
        white_point=round(white_point, 1),
        temperature=round(temperature, 2),
        tint=round(tint, 2),
        saturation_mean=round(saturation_mean, 1),
        saturation_std=round(saturation_std, 1),
        dominant_hue=round(dominant_hue, 1),
        hue_concentration=round(hue_concentration, 3),
    )


HUE_NAMES = {
    0: "빨강", 15: "주황", 30: "노랑", 45: "연두",
    60: "초록", 75: "청록", 90: "시안", 105: "하늘",
    120: "파랑", 135: "남색", 150: "보라", 165: "자홍",
}


def hue_to_name(hue: float) -> str:
    nearest = min(HUE_NAMES.keys(), key=lambda k: abs(k - hue))
    return HUE_NAMES[nearest]


def generate_preset(profiles: list[ToneProfile]) -> dict:
    """레퍼런스 프로파일들의 평균으로 베이스 프리셋 생성"""
    def avg(field: str) -> float:
        return round(float(np.mean([getattr(p, field) for p in profiles])), 2)

    def std(field: str) -> float:
        return round(float(np.std([getattr(p, field) for p in profiles])), 2)

    target = {
        "brightness":  {"target": avg("brightness_mean"), "tolerance": std("brightness_mean")},
        "contrast":    {"target": avg("brightness_std"),  "tolerance": std("brightness_std")},
        "black_point": {"target": avg("black_point"),     "tolerance": std("black_point")},
        "white_point": {"target": avg("white_point"),     "tolerance": std("white_point")},
        "temperature": {"target": avg("temperature"),     "tolerance": std("temperature")},
        "tint":        {"target": avg("tint"),            "tolerance": std("tint")},
        "saturation":  {"target": avg("saturation_mean"), "tolerance": std("saturation_mean")},
    }

    return target


def save_histogram(profiles: list[ToneProfile], output_path: str):
    """분석 결과 히스토그램 시각화 저장"""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 3, figsize=(14, 8))
        fig.suptitle("Reference Feed Tone Profile", fontsize=14, fontweight="bold")

        metrics = [
            ("brightness_mean", "Brightness (L)", "darkblue"),
            ("brightness_std", "Contrast (L std)", "purple"),
            ("temperature", "Temperature (b*)", "orangered"),
            ("saturation_mean", "Saturation (S)", "green"),
            ("black_point", "Black Point (L 5%)", "black"),
            ("white_point", "White Point (L 95%)", "gold"),
        ]

        for ax, (field, title, color) in zip(axes.flat, metrics):
            values = [getattr(p, field) for p in profiles]
            ax.bar(range(len(values)), values, color=color, alpha=0.7)
            ax.axhline(y=np.mean(values), color="red", linestyle="--", linewidth=1.5, label=f"avg={np.mean(values):.1f}")
            ax.set_title(title, fontsize=10)
            ax.legend(fontsize=8)
            ax.tick_params(axis="x", labelsize=7)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        print(f"\n📊 히스토그램 저장: {output_path}")
    except ImportError:
        print("\n[INFO] matplotlib 미설치. 히스토그램 생략. pip install matplotlib")


def main():
    if len(sys.argv) < 2:
        print("Usage: python tone_profiler.py <이미지_폴더_경로>")
        print("예시:  python tone_profiler.py C:\\Users\\SSAFY\\Downloads\\reference_feed")
        sys.exit(1)

    folder = Path(sys.argv[1])
    if not folder.is_dir():
        print(f"Error: {folder} 는 폴더가 아닙니다.")
        sys.exit(1)

    # 이미지 파일 수집
    extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    image_files = sorted([f for f in folder.iterdir() if f.suffix.lower() in extensions])

    if not image_files:
        print(f"Error: {folder} 에 이미지 파일이 없습니다.")
        sys.exit(1)

    print(f"📁 {folder} — {len(image_files)}개 이미지 분석 시작\n")

    # ── 개별 분석 ──
    profiles: list[ToneProfile] = []
    for img_path in image_files:
        profile = analyze_image(str(img_path))
        if profile:
            profiles.append(profile)
            hue_name = hue_to_name(profile.dominant_hue)
            print(f"  ✅ {profile.filename}")
            print(f"     밝기={profile.brightness_mean} (std={profile.brightness_std})")
            print(f"     블랙포인트={profile.black_point}  화이트포인트={profile.white_point}")
            print(f"     색온도={profile.temperature:+.1f}  색조={profile.tint:+.1f}")
            print(f"     채도={profile.saturation_mean}  지배색={hue_name}({profile.dominant_hue}°, {profile.hue_concentration:.0%})")
            print()

    if not profiles:
        print("분석 가능한 이미지가 없습니다.")
        sys.exit(1)

    # ── 목표 톤 프로파일 (전체 평균) ──
    print("=" * 60)
    print(f"📐 목표 톤 프로파일 ({len(profiles)}장 평균)")
    print("=" * 60)

    target = generate_preset(profiles)
    for key, val in target.items():
        unit = ""
        if key == "brightness":
            unit = " (0=검정, 255=백색)"
        elif key == "temperature":
            unit = " (+따뜻, −차가움)"
        elif key == "saturation":
            unit = " (0=무채색, 255=원색)"

        print(f"  {key:14s}: 목표={val['target']:>7.1f}  허용범위=±{val['tolerance']:.1f}{unit}")

    # ── 해석 ──
    print("\n" + "=" * 60)
    print("📖 해석")
    print("=" * 60)

    b = target["brightness"]["target"]
    c = target["contrast"]["target"]
    t = target["temperature"]["target"]
    s = target["saturation"]["target"]
    bp = target["black_point"]["target"]

    tone_desc = []
    if b < 100:
        tone_desc.append("상당히 어두운 톤")
    elif b < 130:
        tone_desc.append("약간 어두운 톤")
    elif b < 160:
        tone_desc.append("중간 밝기")
    else:
        tone_desc.append("밝은 톤")

    if t > 3:
        tone_desc.append("따뜻한 색온도")
    elif t > 0:
        tone_desc.append("약간 따뜻한 색온도")
    elif t > -3:
        tone_desc.append("약간 차가운 색온도")
    else:
        tone_desc.append("차가운 색온도")

    if s < 60:
        tone_desc.append("매우 뮤트된 채도")
    elif s < 90:
        tone_desc.append("뮤트 채도")
    elif s < 120:
        tone_desc.append("보통 채도")
    else:
        tone_desc.append("비비드 채도")

    if bp > 20:
        tone_desc.append("리프트드 블랙(페이드/매트 효과)")
    else:
        tone_desc.append("딥 블랙")

    if c < 40:
        tone_desc.append("로우 콘트라스트")
    elif c < 55:
        tone_desc.append("미디엄 콘트라스트")
    else:
        tone_desc.append("하이 콘트라스트")

    print(f"  스타일: {' · '.join(tone_desc)}")

    # ── JSON 저장 ──
    output = {
        "preset_name": "custom_aesthetic",
        "description": " · ".join(tone_desc),
        "reference_count": len(profiles),
        "target_tone": target,
        "individual_profiles": [asdict(p) for p in profiles],
    }

    json_path = folder / "tone_profile.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n💾 프로파일 저장: {json_path}")

    # ── 히스토그램 ──
    save_histogram(profiles, str(folder / "tone_histogram.png"))

    # ── 에이전트 적용 가이드 ──
    print("\n" + "=" * 60)
    print("🔧 에이전트 적용 방법")
    print("=" * 60)
    print(f"""
  새 사진이 들어오면:
    1. 동일한 analyze_image()로 새 사진의 현재 프로파일 추출
    2. 현재값과 목표값의 갭(delta) 계산:
       delta_brightness  = {b:.1f} - 현재_brightness
       delta_temperature = {t:.1f} - 현재_temperature
       delta_saturation  = {s:.1f} - 현재_saturation
    3. delta를 OpenCV 보정 파라미터로 변환하여 적용
    4. 허용범위(tolerance) 안이면 보정 스킵 → 과보정 방지
""")


if __name__ == "__main__":
    main()