import { useEffect } from "react"
import confetti from "canvas-confetti"
import CharacterLove from "@/assets/character/CharacterLove.png"
import CharacterFail from "@/assets/character/CharacterFail.png"
import StepProgress from "@/components/common/StepProgress"
import Button from "@/components/common/Button"

export default function PublishResultStep({ type, stepNum, onGoHome, onViewInstagram, onRetry }) {
	const isSuccess = type === "success"

	useEffect(() => {
		if (isSuccess) {
			confetti({
				particleCount: 100,
				spread: 70,
				origin: { y: 0.6 },
				colors: ['#ff7a3d', '#facc15', '#4ade80'],
				zIndex: 100,
			})
		}
	}, [isSuccess])

	return (
		<main className="flex h-dvh flex-col items-center bg-white px-5 pt-6">
			{/* 진행바 */}
			<section className="flex w-full justify-center pb-5 px-6">
				<StepProgress current={stepNum} />
			</section>

			{/* 텍스트 */}
			<section className="flex h-40 items-center justify-center">
				<h1 className="text-center text-[28px] font-bold leading-snug text-accent-100">
					{isSuccess ? (
						<>발행 성공!<br />고생하셨습니다.</>
					) : (
						"발행 실패!"
					)}
				</h1>
			</section>

			{/* 캐릭터 이미지 */}
			<div className="flex flex-1 items-center justify-center">
				<img
					src={isSuccess ? CharacterLove : CharacterFail}
					alt={isSuccess ? "발행 성공 캐릭터" : "발행 실패 캐릭터"}
					className="object-contain"
				/>
			</div>

			{/* 버튼 */}
			<section className="flex w-full flex-col items-center gap-3 pb-10">
				{isSuccess ? (
					<Button variant="instagram" size="lg" onClick={onViewInstagram} className="shadow-lg shadow-gray-300">
						에서 보기
					</Button>
				) : (
					<Button variant="primary" size="lg" onClick={onRetry} className="shadow-lg shadow-gray-300">
						다시 발행하기
					</Button>
				)}
				<Button variant="navy" size="lg" onClick={onGoHome} className="shadow-lg shadow-gray-300">
					홈으로 돌아가기
				</Button>
			</section>
		</main>
	)
}
