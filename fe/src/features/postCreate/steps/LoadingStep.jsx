import StepProgress from "@/components/common/StepProgress"
import TitleText from "@/components/common/TitleText"
import Character from "@/components/common/Character"

export default function LoadingStep({ title, description, stepNum }) {
	return (
		<main className="relative flex h-dvh overflow-hidden justify-center bg-surface-50">
			<div className="h-full w-full max-w-md px-5 py-6 pb-60">
				<section className="flex justify-center pt-2">
					<StepProgress current={stepNum} />
				</section>

				<section className="flex h-40 items-center justify-center">
					<div>
						<TitleText text={title} />
						{description ? <p className="mt-3 text-center text-gray-500">{description}</p> : null}
					</div>
				</section>

				<section className="flex justify-center">
					<Character type="run" />
				</section>
			</div>
		</main>
	)
}
