import { useEffect, useRef, useState } from "react"
import StepProgress from "@/components/common/StepProgress"
import Button from "@/components/common/Button"
import BottomTab from "@/components/common/BottomTab"

const PEEK = 0

export default function GeneratedPostStep({ post, photos = [], onPublish, onExit, stepNum }) {
	const [activeIndex, setActiveIndex] = useState(0)
	const [isBodyScrollable, setIsBodyScrollable] = useState(false)
	const [canScrollDown, setCanScrollDown] = useState(false)
	const [hasDelayPassed, setHasDelayPassed] = useState(false)
	const [hasUserScrolled, setHasUserScrolled] = useState(false)
	const contentSectionRef = useRef(null)

	const handleScroll = (e) => {
		const el = e.currentTarget
		const cardWidth = el.offsetWidth
		const idx = Math.round(el.scrollLeft / cardWidth)
		setActiveIndex(Math.max(0, Math.min(idx, photos.length - 1)))
	}

	const updateBodyScrollState = (el) => {
		if (!el) return
		const scrollable = el.scrollHeight > el.clientHeight
		const hasMoreBelow = scrollable && el.scrollTop + el.clientHeight < el.scrollHeight - 1
		setIsBodyScrollable(scrollable)
		setCanScrollDown(hasMoreBelow)
	}

	const handleBodyScroll = (e) => {
		const el = e.currentTarget
		if (el.scrollTop > 0) setHasUserScrolled(true)
		updateBodyScrollState(el)
	}

	const shouldShowChevron = hasDelayPassed && canScrollDown && !hasUserScrolled

	useEffect(() => {
		const checkBodyScrollable = () => {
			updateBodyScrollState(contentSectionRef.current)
		}

		const rafId = requestAnimationFrame(checkBodyScrollable)
		window.addEventListener("resize", checkBodyScrollable)
		return () => {
			cancelAnimationFrame(rafId)
			window.removeEventListener("resize", checkBodyScrollable)
		}
	}, [post?.content, post?.hashtags])

	useEffect(() => {
		setHasDelayPassed(false)
		setHasUserScrolled(false)

		const timer = window.setTimeout(() => {
			setHasDelayPassed(true)
		}, 2000)

		return () => window.clearTimeout(timer)
	}, [post?.content, post?.hashtags])

	return (
		<main className="relative flex h-dvh flex-col bg-white">
			{/* 상단 진행바 */}
			<section className="flex justify-center px-5 pt-6 pb-3 shrink-0">
				<StepProgress current={stepNum} />
			</section>

			<section
				ref={contentSectionRef}
				onScroll={handleBodyScroll}
				data-scrollable={isBodyScrollable}
				className="relative flex flex-1 flex-col overflow-y-auto pb-20"
			>
				{/* 사진 캐러셀 */}
				<section className="shrink-0 w-full">
					<div
						onScroll={handleScroll}
						className="flex w-full snap-x snap-mandatory overflow-x-auto"
						style={{ scrollbarWidth: "none", WebkitOverflowScrolling: "touch" }}
					>
						{photos.length > 0 ? photos.map((photo, i) => (
							<div
								key={photo.id ?? i}
								className="relative shrink-0 snap-center w-full aspect-[384/514] overflow-hidden"
							>
								{photo.url
									? <img src={photo.url} alt={`photo-${i + 1}`} className="h-full w-full object-cover" draggable={false} />
									: <div className="h-full w-full bg-primary-100" />
								}
								{photos.length > 1 && (
									<div className="absolute top-4 right-4 rounded-full bg-accent-100/80 px-3 py-1 text-sm font-semibold text-white">
										{i + 1} / {photos.length}
									</div>
								)}
							</div>
						)) : (
							<div className="relative shrink-0 snap-center w-full aspect-[384/514] bg-primary-100">
								<div className="absolute top-4 right-4 rounded-full bg-accent-100/80 px-3 py-1 text-sm font-semibold text-white">
									1 / 1
								</div>
							</div>
						)}
					</div>
				</section>

				<section className="px-5 pt-5">
					<h2 className="text-xl font-bold text-accent-100 mb-3">본문</h2>
					<div className="rounded-2xl bg-gray-50 px-5 py-4 text-lg text-accent-100 leading-relaxed whitespace-pre-wrap">
						<p className="mb-4">{post?.content ?? ""}</p>
						<p className="text-accent-100">{post?.hashtags?.join(" ") ?? ""}</p>
					</div>
				</section>

				{/* 버튼 */}
				<div className="flex items-center justify-center gap-3 px-5 pt-5 pb-2">
					<Button variant="white" size="sm" onClick={onExit}>나가기</Button>
					<Button variant="primary" size="sm" onClick={onPublish}>발행하기</Button>
				</div>
			</section>

			<div
				className={`pointer-events-none absolute inset-x-0 bottom-20 z-10 h-24 bg-gradient-to-t from-black/20 to-transparent transition-opacity duration-200 ${shouldShowChevron ? "opacity-100" : "opacity-0"}`}
				aria-hidden="true"
			/>

			<div
				className={`pointer-events-none absolute bottom-20 left-1/2 z-20 -translate-x-1/2 transition-opacity duration-200 ${shouldShowChevron ? "opacity-100 animate-bounce" : "opacity-0"}`}
				aria-hidden="true"
			>
				<svg viewBox="0 0 50 30" className="h-7 w-10" fill="none" xmlns="http://www.w3.org/2000/svg">
					<path d="M4 4L25 25L46 4" stroke="#FF8A3D" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" />
				</svg>
			</div>

			<BottomTab />
		</main>
	)
}

