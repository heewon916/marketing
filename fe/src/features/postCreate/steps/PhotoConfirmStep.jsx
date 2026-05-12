import { useEffect, useRef, useState } from "react"
import StepProgress from "@/components/common/StepProgress"
import Button from "@/components/common/Button"
import BottomTab from "@/components/common/BottomTab"
import PhotoConfirmCarousel from "@/features/postCreate/components/PhotoConfirmCarousel"
import PhotoDeleteButton from "@/features/postCreate/components/PhotoDeleteButton"
import PhotoConfirmSkeleton from "@/features/postCreate/components/PhotoConfirmSkeleton"
import { requestContentImages, requestDeleteContentImage } from "@/features/postCreate/api/ImageApi"

const PEEK = 30
const GAP = 16

export default function PhotoConfirmStep({ sessionId, photos: initialPhotos = [], onNext, onLeaveHomeConfirm, stepNum }) {
	const [photos, setPhotos] = useState(initialPhotos)
	const [activeIndex, setActiveIndex] = useState(0)
	const [isLoading, setIsLoading] = useState(Boolean(sessionId))
	const [isDeleting, setIsDeleting] = useState(false)
	const [errorMessage, setErrorMessage] = useState("")
	const trackRef = useRef(null)

	useEffect(() => {
		let isMounted = true

		const loadImages = async () => {
			if (!sessionId) {
				setIsLoading(false)
				return
			}

			setIsLoading(true)
			setErrorMessage("")

			try {
				const result = await requestContentImages(sessionId)

				if (!isMounted) {
					return
				}

				setPhotos(result.images)
				setActiveIndex(0)
			} catch (error) {
				if (isMounted) {
					setErrorMessage(error.message || "이미지를 불러오지 못했습니다.")
				}
			} finally {
				if (isMounted) {
					setIsLoading(false)
				}
			}
		}

		loadImages()

		return () => {
			isMounted = false
		}
	}, [sessionId])

	const handleScroll = () => {
		const el = trackRef.current
		if (!el) return
		const cardWidth = el.offsetWidth - PEEK * 2
		const idx = Math.round(el.scrollLeft / (cardWidth + GAP))
		setActiveIndex(Math.max(0, Math.min(idx, photos.length - 1)))
	}

	const deleteDisabled = photos.length <= 1 || isDeleting

	const handleDelete = async () => {
		if (deleteDisabled) return

		const targetPhoto = photos[activeIndex]
		const deletedImageKey = targetPhoto?.imageKey

		if (!deletedImageKey) {
			window.alert("삭제할 이미지 키를 찾지 못했습니다.")
			return
		}

		setIsDeleting(true)

		try {
			await requestDeleteContentImage(sessionId, deletedImageKey)
		} catch (error) {
			window.alert(error.message || "이미지 삭제에 실패했습니다.")
			setIsDeleting(false)
			return
		}

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

		setIsDeleting(false)
	}

	if (isLoading) {
		return <PhotoConfirmSkeleton />
	}

	if (errorMessage) {
		return (
			<main className="flex h-dvh flex-col items-center justify-center bg-white gap-6 px-6 text-center">
				<p className="text-lg text-gray-500">{errorMessage}</p>
				<Button variant="white" size="sm" onClick={onLeaveHomeConfirm}>나가기</Button>
			</main>
		)
	}

	if (photos.length === 0) {
		return (
			<main className="flex h-dvh flex-col items-center justify-center bg-white gap-6">
				<p className="text-lg text-gray-400">사진이 없어요</p>
				<Button variant="white" size="sm" onClick={onLeaveHomeConfirm}>나가기</Button>
			</main>
		)
	}

	return (
		<main className="relative flex h-dvh flex-col bg-white">
			{/* 상단 진행바 */}
			<section className="flex justify-center px-10 pt-8 pb-3 shrink-0">
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

				<PhotoDeleteButton onClick={handleDelete} disabled={deleteDisabled} />
			</section>

			{/* 하단 버튼 */}
			<section className="fixed bottom-20 left-1/2 z-20 w-full max-w-md -translate-x-1/2 px-4 pb-4">
				<div className="flex items-center justify-center gap-3">
					<Button variant="white" size="sm" onClick={onLeaveHomeConfirm}>나가기</Button>
					<Button variant="primary" size="sm" onClick={() => onNext?.(photos)}>글 확인</Button>
				</div>
			</section>

			<BottomTab />
		</main>
	)
}
