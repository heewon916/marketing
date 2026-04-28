import { useEffect, useState } from "react"
import StepProgress from "@/components/common/StepProgress"
import CharacterRun from "@/assets/character/CharacterRun.png"

const TOTAL_CARDS = 3

function PhotoCard({ state, src }) {
	if (state === "loaded") {
		return (
			<div className="aspect-square w-full overflow-hidden rounded-2xl bg-gray-200">
				{src ? (
					<img src={src} alt="추출된 사진" className="h-full w-full object-cover" />
				) : (
					<div className="h-full w-full bg-gradient-to-br from-amber-100 to-orange-200" />
				)}
			</div>
		)
	}

	if (state === "loading") {
		return (
			<div className="relative aspect-square w-full overflow-hidden rounded-2xl bg-gray-200">
				<div className="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/70 to-transparent" />
				<p className="absolute inset-0 flex items-center justify-center text-xs text-gray-400">
					로딩중
				</p>
			</div>
		)
	}

	// waiting
	return (
		<div className="flex aspect-square w-full items-center justify-center rounded-2xl bg-gray-100">
			<p className="text-xs text-gray-400">대기중</p>
		</div>
	)
}

export default function ExtractLoadingStep({ stepNum, photos = [] }) {
	const [animatedCount, setAnimatedCount] = useState(0)

	// 800ms마다 카드 한 장씩 "로딩 → 완료"로 전환
	useEffect(() => {
		if (animatedCount >= TOTAL_CARDS) return
		const timer = setTimeout(() => setAnimatedCount((c) => c + 1), 2500)
		return () => clearTimeout(timer)
	}, [animatedCount])

	return (
		<main className="relative flex h-dvh justify-center bg-surface-50">
			<div className="flex h-full w-full max-w-md flex-col px-5 py-6">
				<section className="flex justify-center pt-2">
					<StepProgress current={stepNum} />
				</section>

				<section className="flex justify-center py-10">
					<h1
						className="text-center text-3xl font-medium text-accent-500"
						style={{ wordBreak: "keep-all" }}
					>
						영상에서
						<br />
						가게의 멋진 사진을
						<br />
						가져오는 중...
					</h1>
				</section>

				<section className="flex flex-1 items-center justify-center">
					<img src={CharacterRun} alt="로딩 중 캐릭터" className="max-h-64 object-contain" />
				</section>

				<section className="grid grid-cols-3 gap-3 pb-6">
					{Array.from({ length: TOTAL_CARDS }).map((_, i) => {
						const src = photos[i]?.url
						if (i < animatedCount) {
							return <PhotoCard key={i} state="loaded" src={src} />
						} else if (i === animatedCount) {
							return <PhotoCard key={i} state="loading" />
						} else {
							return <PhotoCard key={i} state="waiting" />
						}
					})}
				</section>
			</div>
		</main>
	)
}
