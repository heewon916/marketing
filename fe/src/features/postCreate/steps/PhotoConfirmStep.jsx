import { useRef, useState } from "react"
import StepProgress from "@/components/common/StepProgress"
import Button from "@/components/common/Button"
import BottomTab from "@/components/common/BottomTab"
import PhotoConfirmCarousel from "@/features/postCreate/components/PhotoConfirmCarousel"
import PhotoDeleteButton from "@/features/postCreate/components/PhotoDeleteButton"

const PEEK = 30
const GAP = 16

export default function PhotoConfirmStep({ photos: initialPhotos = [], onNext, onRetake, stepNum }) {
	const [photos, setPhotos] = useState(initialPhotos)
	const [activeIndex, setActiveIndex] = useState(0)
	const trackRef = useRef(null)

	const handleScroll = () => {
		const el = trackRef.current
		if (!el) return
		const cardWidth = el.offsetWidth - PEEK * 2
		const idx = Math.round(el.scrollLeft / (cardWidth + GAP))
		setActiveIndex(Math.max(0, Math.min(idx, photos.length - 1)))
	}

	const handleDelete = () => {
		if (photos.length === 0) return
		const next = photos.filter((_, i) => i !== activeIndex)
		const newIdx = Math.min(activeIndex, next.length - 1)
		setPhotos(next)
		setActiveIndex(newIdx)
		const el = trackRef.current
		if (el && next.length > 0) {
			const cardWidth = el.offsetWidth - PEEK * 2
			setTimeout(() => {
				el.scrollTo({ left: newIdx * (cardWidth + GAP), behavior: "instant" })
			}, 0)
		}
	}

	if (photos.length === 0) {
		return (
			<main className="flex h-dvh flex-col items-center justify-center bg-white gap-6">
				<p className="text-lg text-gray-400">사진이 없어요</p>
				<Button variant="white" size="sm" onClick={onRetake}>다시 촬영</Button>
			</main>
		)
	}

	return (
		<main className="relative flex h-dvh flex-col bg-white">
			{/* 상단 진행바 */}
			<section className="flex justify-center px-5 pt-6 pb-4 shrink-0">
				<StepProgress current={stepNum} />
			</section>

			{/* 캐러셀 + 휴지통 */}
			<section className="flex flex-col flex-1 items-center justify-center overflow-hidden gap-5 pb-40">
				<PhotoConfirmCarousel
					photos={photos}
					trackRef={trackRef}
					onScroll={handleScroll}
					peek={PEEK}
					gap={GAP}
				/>

				<PhotoDeleteButton onClick={handleDelete} />
			</section>

			{/* 하단 버튼 */}
			<section className="fixed bottom-20 left-1/2 z-20 w-full max-w-md -translate-x-1/2 px-4 pb-4">
				<div className="flex items-center justify-center gap-3">
					<Button variant="white" size="sm" onClick={onRetake}>다시 촬영</Button>
					<Button variant="primary" size="sm" onClick={() => onNext?.(photos)}>글 확인</Button>
				</div>
			</section>

			<BottomTab />
		</main>
	)
}
