import { useEffect, useMemo, useRef, useState } from "react"

const VIDEO_TYPES = ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm"]
const MAX_RECORD_SECONDS = 60
const TARGET_ASPECT_RATIO = 3 / 4
const MAX_CANVAS_LONG_SIDE = 4096
const OUTPUT_FPS = 60

export default function CameraStep({ onRecorded, onClose }) {
	const videoRef = useRef(null)
	const streamRef = useRef(null)
	const canvasRef = useRef(null)
	const canvasStreamRef = useRef(null)
	const drawFrameRef = useRef(null)
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

		const scoreRearCameraLabel = (label) => {
			if (!label) {
				return 0
			}

			const normalized = label.toLowerCase()
			let score = 0

			if (/back|rear|environment|후면/.test(normalized)) {
				score += 30
			}

			if (/main|default|기본|광각|camera\s*0|back\s*camera\s*0|rear\s*camera\s*0/.test(normalized)) {
				score += 10
			}

			if (/^back\s*camera$|^rear\s*camera$/.test(normalized)) {
				score += 20
			}

			if (/ultra|0\.5|0,5|초광각|uw/.test(normalized)) {
				score -= 100
			}

			if (/tele|망원|periscope/.test(normalized)) {
				score -= 30
			}

			if (/camera\s*[1-9]/.test(normalized)) {
				score -= 8
			}

			return score
		}

		const inspectRearCamera = async (deviceId) => {
			let stream = null

			try {
				stream = await navigator.mediaDevices.getUserMedia({
					video: {
						deviceId: { exact: deviceId },
						facingMode: { ideal: "environment" },
					},
					audio: false,
				})

				const track = stream.getVideoTracks()[0]
				const capabilities = track?.getCapabilities?.() ?? {}
				const zoom = capabilities.zoom
				const minZoom = typeof zoom?.min === "number" ? zoom.min : null
				const maxZoom = typeof zoom?.max === "number" ? zoom.max : null

				return {
					minZoom,
					maxZoom,
					hasZoom: minZoom !== null && maxZoom !== null,
				}
			} catch {
				return null
			} finally {
				stream?.getTracks().forEach((track) => track.stop())
			}
		}

		const getPreferredRearCameraId = async () => {
			let probeStream = null

			try {
				probeStream = await navigator.mediaDevices.getUserMedia({
					video: { facingMode: { ideal: "environment" } },
					audio: false,
				})

				const fallbackDeviceId = probeStream.getVideoTracks()[0]?.getSettings?.()?.deviceId
				const devices = await navigator.mediaDevices.enumerateDevices()
				const rearDevices = devices.filter(
					(device) =>
						device.kind === "videoinput" && /back|rear|environment|후면|camera 0/.test(device.label.toLowerCase())
				)

				if (!rearDevices.length) {
					return fallbackDeviceId ?? null
				}

				let bestDeviceId = null
				let bestScore = Number.NEGATIVE_INFINITY

				for (const device of rearDevices) {
					const inspect = await inspectRearCamera(device.deviceId)
					let score = scoreRearCameraLabel(device.label)

					if (inspect?.hasZoom) {
						const { minZoom, maxZoom } = inspect
						const supportsOneX = minZoom <= 1 && maxZoom >= 1
						score += supportsOneX ? 40 : -40
						score -= Math.abs(minZoom - 1) * 60

						if (minZoom < 0.8) {
							score -= 40
						}

						if (minZoom > 1.2) {
							score -= 20
						}
					}

					if (score > bestScore) {
						bestScore = score
						bestDeviceId = device.deviceId
					}
				}

				return bestDeviceId ?? fallbackDeviceId ?? null
			} catch {
				return null
			} finally {
				probeStream?.getTracks().forEach((track) => track.stop())
			}
		}

		const setupCamera = async () => {
			try {
				const preferredRearCameraId = await getPreferredRearCameraId()
				let stream

				try {
					stream = await navigator.mediaDevices.getUserMedia({
						video: preferredRearCameraId
							? { deviceId: { exact: preferredRearCameraId }, facingMode: { ideal: "environment" } }
							: { facingMode: { ideal: "environment" } },
						audio: true,
					})
				} catch {
					stream = await navigator.mediaDevices.getUserMedia({
						video: { facingMode: { ideal: "environment" } },
						audio: true,
					})
				}

				if (!isMounted) {
					stream.getTracks().forEach((track) => track.stop())
					return
				}

				streamRef.current = stream

				const videoTrack = stream.getVideoTracks()[0]
				const zoomCapability = videoTrack?.getCapabilities?.()?.zoom
				if (videoTrack && zoomCapability) {
					try {
						const initialZoom = Math.min(Math.max(1, zoomCapability.min), zoomCapability.max)
						await videoTrack.applyConstraints({
							advanced: [{ zoom: initialZoom }],
						})
					} catch {
						// Ignore devices/browsers that report zoom but fail to apply it.
					}
				}

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

			if (drawFrameRef.current) {
				cancelAnimationFrame(drawFrameRef.current)
				drawFrameRef.current = null
			}

			canvasStreamRef.current?.getTracks().forEach((track) => track.stop())
			canvasStreamRef.current = null

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

	const startCanvasRendering = () => {
		const video = videoRef.current
		if (!video || !canvasRef.current) {
			return false
		}

		if (!video.videoWidth || !video.videoHeight) {
			return false
		}

		const getOutputSize = (sourceWidth, sourceHeight) => {
			let outputWidth = sourceWidth
			let outputHeight = sourceHeight
			const sourceRatio = sourceWidth / sourceHeight

			if (sourceRatio > TARGET_ASPECT_RATIO) {
				outputWidth = Math.round(sourceHeight * TARGET_ASPECT_RATIO)
				outputHeight = sourceHeight
			} else {
				outputWidth = sourceWidth
				outputHeight = Math.round(sourceWidth / TARGET_ASPECT_RATIO)
			}

			const longSide = Math.max(outputWidth, outputHeight)
			if (longSide > MAX_CANVAS_LONG_SIDE) {
				const scale = MAX_CANVAS_LONG_SIDE / longSide
				outputWidth = Math.round(outputWidth * scale)
				outputHeight = Math.round(outputHeight * scale)
			}

			if (outputWidth % 2 !== 0) {
				outputWidth -= 1
			}

			if (outputHeight % 2 !== 0) {
				outputHeight -= 1
			}

			return {
				width: Math.max(2, outputWidth),
				height: Math.max(2, outputHeight),
			}
		}

		const canvas = canvasRef.current
		const { width, height } = getOutputSize(video.videoWidth, video.videoHeight)
		canvas.width = width
		canvas.height = height
		const context = canvas.getContext("2d", { alpha: false })

		if (!context) {
			return false
		}

		const draw = () => {
			if (!video.videoWidth || !video.videoHeight) {
				drawFrameRef.current = requestAnimationFrame(draw)
				return
			}

			const sourceWidth = video.videoWidth
			const sourceHeight = video.videoHeight
			const targetRatio = TARGET_ASPECT_RATIO
			const sourceRatio = sourceWidth / sourceHeight

			let sx = 0
			let sy = 0
			let sWidth = sourceWidth
			let sHeight = sourceHeight

			if (sourceRatio > targetRatio) {
				sWidth = sourceHeight * targetRatio
				sx = (sourceWidth - sWidth) / 2
			} else {
				sHeight = sourceWidth / targetRatio
				sy = (sourceHeight - sHeight) / 2
			}

			context.drawImage(video, sx, sy, sWidth, sHeight, 0, 0, canvas.width, canvas.height)
			drawFrameRef.current = requestAnimationFrame(draw)
		}

		draw()
		return true
	}

	const stopCanvasRendering = () => {
		if (drawFrameRef.current) {
			cancelAnimationFrame(drawFrameRef.current)
			drawFrameRef.current = null
		}

		canvasStreamRef.current?.getTracks().forEach((track) => track.stop())
		canvasStreamRef.current = null
	}

	const startRecording = () => {
		if (!streamRef.current || !mimeType) {
			setErrorMessage("이 브라우저에서는 영상 녹화를 시작할 수 없습니다.")
			return
		}

		try {
			if (!startCanvasRendering()) {
				setErrorMessage("카메라 준비가 완료된 뒤 다시 시도해주세요.")
				return
			}

			shouldEmitRecordingRef.current = true
			chunksRef.current = []
			setRemainingSeconds(MAX_RECORD_SECONDS)

			const canvasStream = canvasRef.current.captureStream(OUTPUT_FPS)
			canvasStreamRef.current = canvasStream

			const recordingStream = new MediaStream()
			canvasStream.getVideoTracks().forEach((track) => recordingStream.addTrack(track))
			streamRef.current.getAudioTracks().forEach((track) => recordingStream.addTrack(track))

			const mediaRecorder = new MediaRecorder(recordingStream, { mimeType })
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

				stopCanvasRendering()

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
			stopCanvasRendering()
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

			<section className="relative mt-4 w-full shrink-0 aspect-[3/4] overflow-hidden rounded-[15px] bg-[#1f1f1f]">
				<video ref={videoRef} autoPlay muted playsInline className="h-full w-full object-cover opacity-70" />
				<canvas ref={canvasRef} className="hidden" />
				<div className="absolute inset-0 bg-black/20" />

				<div className="pointer-events-none absolute inset-0 flex items-center justify-center px-16 py-24">
					<div className="h-full w-full rounded-[12px] border-[6px] border-[#ef4444]" />
				</div>
			</section>

			{errorMessage ? <p className="mt-4 text-center text-sm text-red-400">{errorMessage}</p> : null}

			<section className="mt-15 flex items-center justify-center">
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
