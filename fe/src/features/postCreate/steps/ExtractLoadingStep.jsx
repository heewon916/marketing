import { useEffect, useState } from "react"
import StepProgress from "@/components/common/StepProgress"
import TitleText from "@/components/common/TitleText"
import Character from "@/components/common/Character"
//import ExtractPhotoGrid from "@/features/postCreate/components/ExtractPhotoGrid"

const LOADING_MESSAGES = [
	"영상에서\n가게의 멋진 사진을\n가져오는 중...",
	"영상에서\n가장 선명한 장면을\n고르고 있어요...",
	"조금만 기다려주세요\n사진을 정리하고\n있어요...",
]

export default function ExtractLoadingStep({ stepNum, photos = [] }) {
	const [messageIndex, setMessageIndex] = useState(0)

	useEffect(() => {
		const timer = setInterval(() => {
			setMessageIndex((prevIndex) => (prevIndex + 1) % LOADING_MESSAGES.length)
		}, 2000)

		return () => clearInterval(timer)
	}, [])

	return (
		<main className="relative flex h-dvh justify-center bg-surface-50">
			<div className="flex h-full w-full max-w-md flex-col px-5 py-6">
				<section className="flex justify-center pt-2 px-6">
					<StepProgress current={stepNum} />
				</section>

				<section className="flex h-40 items-center justify-center">
					<TitleText text={LOADING_MESSAGES[messageIndex]} className="whitespace-pre-line" />
				</section>

				<section className="flex justify-center">
					<Character type="run" className="max-h-[40vh]" />
				</section>

				{/* <ExtractPhotoGrid photos={photos} /> */}
			</div>
		</main>
	)
}
