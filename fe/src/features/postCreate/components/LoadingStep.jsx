import StepProgress from "@/components/common/StepProgress"
import CharacterRun from "@/assets/character/CharacterRun.png"

export default function LoadingStep({ title, description, stepNum }) {
	return (
		<main className="relative flex h-dvh overflow-hidden justify-center bg-surface-50">
			<div className="h-full w-full max-w-md px-5 py-6 pb-60">
				<section className="flex justify-center pt-2">
					<StepProgress current={stepNum} />
				</section>

				<section className="flex h-40 items-center justify-center">
					<div>
						<h1 className="text-center text-[28px] font-medium text-accent-500" style={{ wordBreak: "keep-all" }}>
							{title}
						</h1>
						{description ? <p className="mt-3 text-center text-gray-500">{description}</p> : null}
					</div>
				</section>

				<section className="flex justify-center">
					<img src={CharacterRun} alt="로딩 중 캐릭터" className="object-contain" />
				</section>
			</div>
		</main>
	)
}
