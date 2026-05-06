import StepProgress from "@/components/common/StepProgress"
import TitleText from "@/components/common/TitleText"
import Character from "@/components/common/Character"
import ExtractPhotoGrid from "@/features/postCreate/components/ExtractPhotoGrid"

export default function ExtractLoadingStep({ stepNum, photos = [] }) {
	return (
		<main className="relative flex h-dvh justify-center bg-surface-50">
			<div className="flex h-full w-full max-w-md flex-col px-5 py-6">
				<section className="flex justify-center pt-2 px-6">
					<StepProgress current={stepNum} />
				</section>

				<section className="flex h-40 items-center justify-center">
					<TitleText text={"영상에서\n가게의 멋진 사진을\n가져오는 중..."} className="whitespace-pre-line" />
				</section>

				<section className="flex flex-1 items-center justify-center">
					<Character type="run" className="max-h-[40vh]" />
				</section>

				<ExtractPhotoGrid photos={photos} />
			</div>
		</main>
	)
}
