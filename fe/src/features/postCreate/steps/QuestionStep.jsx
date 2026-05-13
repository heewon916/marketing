import BottomTab from "@/components/common/BottomTab"
import Button from "@/components/common/Button"
import StepProgress from "@/components/common/StepProgress"
import TitleText from "@/components/common/TitleText"
import Character from "@/components/common/Character"

export default function QuestionStep({
	title,
	stepNum,
	onNext,
	onLeaveHomeConfirm,
	characterSrc,
	characterType,
}) {
	const handleYes = () => {
		onNext?.()
	}

	const handleNo = () => {
		onLeaveHomeConfirm?.()
	}

	return (
		<main className="relative flex h-dvh overflow-hidden justify-center bg-surface-50">
			<div className="h-full w-full max-w-md px-5 py-6 pb-60">
				<section className="flex justify-center pt-2 px-6">
					<StepProgress current={stepNum} />
				</section>

				<section className="flex h-40 items-center justify-center">
					<TitleText text={title} />
				</section>

				   <section className="flex justify-center items-end h-[40vh] min-h-[120px]">
					   <Character src={characterSrc} type={characterType} className="h-full max-h-[40vh] max-w-[80vw] w-auto" />
				   </section>
			</div>

			<section className="fixed bottom-20 left-1/2 z-20 w-full max-w-md -translate-x-1/2">
				<div className="w-full px-4 pb-10">
					<div className="flex items-center justify-center gap-3">
						<Button type="button" size="sm" variant="white" onClick={handleNo}>
							아니오
						</Button>
						<Button type="button" size="sm" variant="primary" onClick={handleYes}>
							예
						</Button>
					</div>
				</div>
			</section>

			<BottomTab />
		</main>
	)
}
