import { useEffect, useRef, useState } from "react"
import StepProgress from "@/components/common/StepProgress"
import Button from "@/components/common/Button"
import BottomTab from "@/components/common/BottomTab"
import GeneratedPostCarousel from "@/features/postCreate/components/GeneratedPostCarousel"
import GeneratedPostBody from "@/features/postCreate/components/GeneratedPostBody"

export default function GeneratedPostStep({ post, photos = [], onPublish, onExit, stepNum }) {
	const [editedContent, setEditedContent] = useState(post?.content ?? "")
	const [editedHashtags, setEditedHashtags] = useState(post?.hashtags ?? [])
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
				<GeneratedPostCarousel photos={photos} onScroll={handleScroll} />

				<GeneratedPostBody
					content={editedContent}
					hashtags={editedHashtags}
					onContentChange={setEditedContent}
					onHashtagsChange={setEditedHashtags}
				/>

				{/* 버튼 */}
				<div className="flex items-center justify-center gap-3 px-5 pt-5 pb-2">
					<Button variant="white" size="sm" onClick={onExit}>나가기</Button>
					<Button variant="primary" size="sm" onClick={() => onPublish?.({ content: editedContent, hashtags: editedHashtags })}>발행하기</Button>
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

