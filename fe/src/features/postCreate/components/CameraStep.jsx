import { useEffect, useMemo, useRef, useState } from "react"

const VIDEO_TYPES = ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm"]
const MAX_RECORD_SECONDS = 60

export default function CameraStep({ onRecorded, onClose }) {
	const videoRef = useRef(null)
	const streamRef = useRef(null)
	const mediaRecorderRef = useRef(null)
	const chunksRef = useRef([])
	const countdownTimerRef = useRef(null)
	const shouldEmitRecordingRef = useRef(true)

	const [isReady, setIsReady] = useState(false)
	const [isRecording, setIsRecording] = useState(false)
	const [remainingSeconds, setRemainingSeconds] = useState(MAX_RECORD_SECONDS)
	const [errorMessage, setErrorMessage] = useState("")

	const mimeType = useMemo(() => {
		if (typeof MediaRecorder === "undefined") {
			return ""
		}

		return VIDEO_TYPES.find((type) => MediaRecorder.isTypeSupported(type)) ?? "video/webm"
	}, [])

	useEffect(() => {
		let isMounted = true

		const setupCamera = async () => {
			try {
				const stream = await navigator.mediaDevices.getUserMedia({
					video: { facingMode: "environment" },
					audio: true,
				})

				if (!isMounted) {
					stream.getTracks().forEach((track) => track.stop())
					return
				}

				streamRef.current = stream

				if (videoRef.current) {
					videoRef.current.srcObject = stream
				}

				setIsReady(true)
				setErrorMessage("")
			} catch {
				setErrorMessage("카메라와 마이크 접근 권한이 필요합니다.")
				setIsReady(false)
			}
		}

		setupCamera()

		return () => {
			isMounted = false
			shouldEmitRecordingRef.current = false

			if (countdownTimerRef.current) {
				clearInterval(countdownTimerRef.current)
			}

			if (mediaRecorderRef.current?.state !== "inactive") {
				mediaRecorderRef.current?.stop()
			}

			streamRef.current?.getTracks().forEach((track) => track.stop())
			streamRef.current = null
		}
	}, [])

	useEffect(() => {
		if (!isRecording) {
			if (countdownTimerRef.current) {
				clearInterval(countdownTimerRef.current)
				countdownTimerRef.current = null
			}
			return
		}

		countdownTimerRef.current = setInterval(() => {
			setRemainingSeconds((prevSeconds) => {
				if (prevSeconds <= 1) {
					if (countdownTimerRef.current) {
						clearInterval(countdownTimerRef.current)
						countdownTimerRef.current = null
					}
					stopRecording()
					return 0
				}

				return prevSeconds - 1
			})
		}, 1000)

		return () => {
			if (countdownTimerRef.current) {
				clearInterval(countdownTimerRef.current)
				countdownTimerRef.current = null
			}
		}
	}, [isRecording])

	const startRecording = () => {
		if (!streamRef.current || !mimeType) {
			setErrorMessage("이 브라우저에서는 영상 녹화를 시작할 수 없습니다.")
			return
		}

		try {
			shouldEmitRecordingRef.current = true
			chunksRef.current = []
			setRemainingSeconds(MAX_RECORD_SECONDS)
			const mediaRecorder = new MediaRecorder(streamRef.current, { mimeType })
			mediaRecorderRef.current = mediaRecorder

			mediaRecorder.ondataavailable = (event) => {
				if (event.data.size > 0) {
					chunksRef.current.push(event.data)
				}
			}

			mediaRecorder.onstop = () => {
				if (countdownTimerRef.current) {
					clearInterval(countdownTimerRef.current)
					countdownTimerRef.current = null
				}

				const blob = new Blob(chunksRef.current, { type: mimeType })
				const timestamp = new Date().toISOString().replace(/[:.]/g, "-")
				const file = new File([blob], `recorded-${timestamp}.webm`, { type: mimeType })
				setIsRecording(false)
				setRemainingSeconds(MAX_RECORD_SECONDS)

				if (shouldEmitRecordingRef.current && blob.size > 0) {
					const downloadUrl = URL.createObjectURL(file)
					const anchor = document.createElement("a")
					anchor.href = downloadUrl
					anchor.download = file.name
					anchor.click()
					URL.revokeObjectURL(downloadUrl)

					onRecorded?.(file)
				}
			}

			mediaRecorder.start()
			setIsRecording(true)
			setErrorMessage("")
		} catch {
			setErrorMessage("영상 녹화를 시작하지 못했습니다.")
		}
	}

	const stopRecording = () => {
		if (mediaRecorderRef.current?.state === "recording") {
			mediaRecorderRef.current.stop()
		}
	}

	return (
		<main className="relative mx-auto flex h-dvh w-full max-w-md flex-col overflow-hidden bg-black px-6 pb-10 pt-6 text-white">
			<header className="flex items-center justify-end">
				<button
					type="button"
					onClick={onClose}
					className="flex h-15 w-5 items-center justify-center rounded-full text-white transition-opacity hover:opacity-80"
					aria-label="촬영 닫기"
				>
					<span className="material-icons text-[40px] leading-none">close</span>
				</button>
			</header>

			<section className="mt-2 flex h-[72px] shrink-0 items-center justify-center text-center">
				{isRecording ? (
					<div className="text-[64px] font-black leading-none text-primary-100">{remainingSeconds}</div>
				) : (
					<h1 className="text-[28px] font-medium leading-tight" style={{ wordBreak: "keep-all" }}>
						촬영할 대상을
						<br />
						<span className="text-primary-100">사각형 안</span>에 맞춰주세요
					</h1>
				)}
			</section>

			<section className="relative mt-4 flex-1 overflow-hidden rounded-[34px] bg-[#1f1f1f]">
				<video ref={videoRef} autoPlay muted playsInline className="h-full w-full object-cover opacity-70" />
				<div className="absolute inset-0 bg-black/20" />

				<div className="pointer-events-none absolute inset-0 flex items-center justify-center px-16 py-24">
					<div className="h-full w-full rounded-[12px] border-[6px] border-[#ef4444]" />
				</div>
			</section>

			{errorMessage ? <p className="mt-4 text-center text-sm text-red-400">{errorMessage}</p> : null}

			<section className="mt-3 flex items-center justify-center">
				<button
					type="button"
					onClick={isRecording ? stopRecording : startRecording}
					disabled={!isReady && !isRecording}
					className="flex h-[100px] w-[100px] items-center justify-center rounded-full bg-white transition-transform disabled:cursor-not-allowed disabled:opacity-40"
					aria-label={isRecording ? "촬영 완료" : "촬영 시작"}
				>
					{isRecording ? (
						<span className="h-10 w-10 bg-black" />
					) : (
						<span className="h-[60px] w-[60px] rounded-full bg-[#ef4444]" />
					)}
				</button>
			</section>
		</main>
	)
}
