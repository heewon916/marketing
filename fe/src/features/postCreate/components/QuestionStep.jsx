import BottomTab from "@/components/common/BottomTab"
import Button from "@/components/common/Button"
import StepProgress from "@/components/common/StepProgress"

export default function QuestionStep({
	title,
	stepNum,
	onNext,
	characterSrc,
	characterAlt,
}) {
	const handleYes = () => {
		onNext?.()
	}

	return (
		<main className="relative flex h-dvh overflow-hidden justify-center bg-surface-50">
			<div className="h-full w-full max-w-md px-5 py-6 pb-60">
				<section className="flex justify-center pt-2">
					<StepProgress current={stepNum} />
				</section>

				<section className="flex h-40 items-center justify-center">
					<h1 className="text-center text-[28px] font-medium text-accent-500" style={{ wordBreak: "keep-all" }}>
						{title}
					</h1>
				</section>

				<section className="flex justify-center">
					<img
						src={characterSrc}
						alt={characterAlt ?? "스텝 캐릭터"}
						className="object-contain"
					/>
				</section>
			</div>

			<section className="fixed bottom-20 left-1/2 z-20 w-full max-w-md -translate-x-1/2">
				<div className="w-full px-4 pb-10">
					<div className="flex items-center justify-center gap-3">
						<Button type="button" size="sm" variant="white" disabled>
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
