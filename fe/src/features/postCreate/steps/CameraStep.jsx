import { useEffect, useMemo, useRef, useState } from "react"

const VIDEO_TYPES = [
  "video/webm;codecs=vp9,opus",
  "video/webm;codecs=vp8,opus",
  "video/webm",
]

const MAX_RECORD_SECONDS = 60
const TARGET_ASPECT_RATIO = 3 / 4
const OUTPUT_FPS = 30

export default function CameraStep({ onRecorded, onClose }) {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const canvasRef = useRef(null)
  const canvasStreamRef = useRef(null)
  const drawFrameRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const cameraDebugLoggedRef = useRef(false)
  const cropDebugLoggedRef = useRef(false)
  const openCameraRef = useRef(null)
  const rearCameraOptionsRef = useRef([])
  const chunksRef = useRef([])
  const countdownTimerRef = useRef(null)
  const shouldEmitRecordingRef = useRef(true)

  const [isReady, setIsReady] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [remainingSeconds, setRemainingSeconds] = useState(MAX_RECORD_SECONDS)
  const [errorMessage, setErrorMessage] = useState("")
  const [rearCameraOptions, setRearCameraOptions] = useState([])
  const [currentCameraDeviceId, setCurrentCameraDeviceId] = useState("")

  const mimeType = useMemo(() => {
    if (typeof MediaRecorder === "undefined") {
      return ""
    }

    return VIDEO_TYPES.find((type) => MediaRecorder.isTypeSupported(type)) ?? "video/webm"
  }, [])

  useEffect(() => {
    let isMounted = true

    const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

    const applyPreferredRearZoom = async (track) => {
      const capabilities = track?.getCapabilities?.() ?? {}
      const zoom = capabilities.zoom

      if (typeof zoom?.min !== "number" || typeof zoom?.max !== "number") {
        return
      }

      const targetZoom = clamp(1, zoom.min, zoom.max)

      try {
        await track.applyConstraints({
          advanced: [{ zoom: targetZoom }],
        })
      } catch {
        // no-op
      }
    }

    const scoreRearCameraLabel = (label) => {
      if (!label) {
        return 0
      }

      const normalized = label.toLowerCase()
      let score = 0

      // 전면 카메라는 강하게 제외
      if (/front|user|전면/.test(normalized)) {
        score -= 1000
      }

      // 후면 카메라 선호
      if (/back|rear|environment|후면/.test(normalized)) {
        score += 50
      }

      // 일반/메인 카메라 선호
      if (/main|default|기본/.test(normalized)) {
        score += 30
      }

      // 1x 카메라 강하게 선호
      if (/\b1x\b|1\.0x|1,0x/.test(normalized)) {
        score += 120
      }

      // 초광각 카메라 강하게 제외
      if (/ultra|ultra\s*wide|wide\s*angle|0\.5|0,5|0\.6|0,6|초광각|uw/.test(normalized)) {
        score -= 200
      }

      // 망원 카메라도 제외
      if (/tele|telephoto|망원|periscope/.test(normalized)) {
        score -= 80
      }

      // camera 0은 기기마다 의미가 달라서 약한 가산점만 부여
      if (/camera\s*0|back\s*camera\s*0|rear\s*camera\s*0/.test(normalized)) {
        score += 3
      }

      return score
    }

    const inspectCamera = async (deviceId) => {
      let stream = null

      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            deviceId: { exact: deviceId },
          },
          audio: false,
        })

        const track = stream.getVideoTracks()[0]
        const settings = track?.getSettings?.() ?? {}
        const capabilities = track?.getCapabilities?.() ?? {}
        const zoom = capabilities.zoom

        const minZoom = typeof zoom?.min === "number" ? zoom.min : null
        const maxZoom = typeof zoom?.max === "number" ? zoom.max : null

        return {
          settings,
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

    const updateRearCameraOptions = (options) => {
      rearCameraOptionsRef.current = options
      setRearCameraOptions(options)
    }

    const getPreferredRearCameraId = async () => {
      let probeStream = null

      try {
        // 권한 확보 + fallback용 후면 카메라 확보
        probeStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" } },
          audio: false,
        })

        const fallbackDeviceId = probeStream.getVideoTracks()[0]?.getSettings?.()?.deviceId
        const devices = await navigator.mediaDevices.enumerateDevices()
          const fallbackDevice = devices.find((device) => device.deviceId === fallbackDeviceId)
          const fallbackGroupId = fallbackDevice?.groupId ?? null

        // 기존처럼 back/rear/camera0만 남기지 말고 전체 videoinput을 후보로 둠
        const videoDevices = devices.filter((device) => device.kind === "videoinput")

        if (!videoDevices.length) {
          return fallbackDeviceId ?? null
        }

        let bestDeviceId = null
        let bestScore = Number.NEGATIVE_INFINITY

        const debugRows = []
        const rearCandidates = []

        for (const device of videoDevices) {
          const inspect = await inspectCamera(device.deviceId)
          let score = scoreRearCameraLabel(device.label)

          // inspect 실패한 카메라는 낮은 점수
          if (!inspect) {
            score -= 50
          }

          // zoom 정보는 보조 판단으로만 사용
          if (inspect?.hasZoom) {
            const { minZoom, maxZoom } = inspect
            const supportsOneX = minZoom <= 1 && maxZoom >= 1

            score += supportsOneX ? 20 : -20
            score -= Math.abs(minZoom - 1) * 30

            // minZoom이 1보다 너무 작으면 초광각 계열일 가능성이 있어 감점
            if (minZoom < 0.8) {
              score -= 40
            }

            // minZoom이 너무 크면 일반 카메라가 아닐 가능성이 있어 감점
            if (minZoom > 1.2) {
              score -= 20
            }
          }

          if (inspect?.settings?.facingMode === "environment") {
            score += 40
          }

          if (inspect?.settings?.facingMode === "user") {
            score -= 300
          }

          if (fallbackGroupId && device.groupId === fallbackGroupId) {
            score += 15
          }

          debugRows.push({
            label: device.label || "(no label)",
            deviceId: device.deviceId,
            score,
            minZoom: inspect?.minZoom,
            maxZoom: inspect?.maxZoom,
            width: inspect?.settings?.width,
            height: inspect?.settings?.height,
            facingMode: inspect?.settings?.facingMode,
          })

          const isLikelyRear =
            inspect?.settings?.facingMode === "environment" ||
            /back|rear|environment|후면/i.test(device.label || "")

          if (isLikelyRear) {
            rearCandidates.push({
              deviceId: device.deviceId,
              label: device.label || "후면 카메라",
              score,
              minZoom: inspect?.minZoom,
              maxZoom: inspect?.maxZoom,
            })
          }

          if (score > bestScore) {
            bestScore = score
            bestDeviceId = device.deviceId
          }
        }

        console.table(debugRows)

        const rearCameraOptionsInOrder = rearCandidates
          .map(({ deviceId, label, minZoom, maxZoom }) => ({
            deviceId,
            label,
            minZoom,
            maxZoom,
          }))

        if (rearCameraOptionsInOrder.length > 0) {
          console.table(
            rearCameraOptionsInOrder.map((candidate, index) => ({
              priority: index + 1,
              deviceId: candidate.deviceId,
              label: candidate.label,
              minZoom: candidate.minZoom,
              maxZoom: candidate.maxZoom,
            }))
          )
        }

        if (isMounted) {
          updateRearCameraOptions(rearCameraOptionsInOrder)
        }

        const secondRearCameraId = rearCameraOptionsInOrder[1]?.deviceId ?? null
        const firstRearCameraId = rearCameraOptionsInOrder[0]?.deviceId ?? null

        return secondRearCameraId ?? firstRearCameraId ?? bestDeviceId ?? fallbackDeviceId ?? null
      } catch {
        return null
      } finally {
        probeStream?.getTracks().forEach((track) => track.stop())
      }
    }

    const setupCamera = async (forcedDeviceId = null) => {
      try {
        const preferredRearCameraId = forcedDeviceId ?? (await getPreferredRearCameraId())
        let stream

        streamRef.current?.getTracks().forEach((track) => track.stop())
        streamRef.current = null

        try {
          stream = await navigator.mediaDevices.getUserMedia({
            video: preferredRearCameraId
              ? {
                  deviceId: { exact: preferredRearCameraId },
                  facingMode: { ideal: "environment" },
                }
              : {
                  facingMode: { ideal: "environment" },
                },
            audio: true,
          })
        } catch {
          stream = await navigator.mediaDevices.getUserMedia({
            video: {
              facingMode: { ideal: "environment" },
            },
            audio: true,
          })
        }

        if (!isMounted) {
          stream.getTracks().forEach((track) => track.stop())
          return
        }

        streamRef.current = stream

        const videoTrack = stream.getVideoTracks()[0]
        await applyPreferredRearZoom(videoTrack)

        const settings = videoTrack?.getSettings?.()
        const capabilities = videoTrack?.getCapabilities?.()

        setCurrentCameraDeviceId(settings?.deviceId ?? preferredRearCameraId ?? "")

        if (!cameraDebugLoggedRef.current) {
          const zoomRange = capabilities?.zoom

          console.groupCollapsed("[CameraDebug] selected track summary")
          console.log("preferredRearCameraId", preferredRearCameraId)
          console.log("settings", {
            deviceId: settings?.deviceId,
            facingMode: settings?.facingMode,
            width: settings?.width,
            height: settings?.height,
            aspectRatio: settings?.aspectRatio,
            frameRate: settings?.frameRate,
          })
          console.log("zoom", {
            min: zoomRange?.min,
            max: zoomRange?.max,
            step: zoomRange?.step,
            appliedTarget: typeof zoomRange?.min === "number" && typeof zoomRange?.max === "number"
              ? clamp(1, zoomRange.min, zoomRange.max)
              : null,
          })
          console.groupEnd()

          cameraDebugLoggedRef.current = true
        }

        console.log("[Camera] selected settings:", settings)
        console.log("[Camera] selected capabilities:", capabilities)

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

    openCameraRef.current = setupCamera

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
      openCameraRef.current = null
    }
  }, [])

  const handleSwitchRearCamera = async () => {
    if (isRecording) {
      return
    }

    const cameraOptions = rearCameraOptionsRef.current

    if (cameraOptions.length <= 1) {
      setErrorMessage("전환 가능한 후면 카메라가 없습니다.")
      return
    }

    const currentIndex = cameraOptions.findIndex(
      (option) => option.deviceId === currentCameraDeviceId
    )

    const nextIndex = currentIndex < 0 ? 0 : (currentIndex + 1) % cameraOptions.length
    const nextCamera = cameraOptions[nextIndex]

    if (!nextCamera?.deviceId || !openCameraRef.current) {
      setErrorMessage("카메라를 전환할 수 없습니다.")
      return
    }

    setIsReady(false)
    setErrorMessage("")
    await openCameraRef.current(nextCamera.deviceId)
  }

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
    const sourceWidth = video.videoWidth
    const sourceHeight = video.videoHeight
    const { width, height } = getOutputSize(video.videoWidth, video.videoHeight)

    const sourceRatio = sourceWidth / sourceHeight
    let cropWidth = sourceWidth
    let cropHeight = sourceHeight

    if (sourceRatio > TARGET_ASPECT_RATIO) {
      cropWidth = sourceHeight * TARGET_ASPECT_RATIO
    } else {
      cropHeight = sourceWidth / TARGET_ASPECT_RATIO
    }

    if (!cropDebugLoggedRef.current) {
      console.groupCollapsed("[CameraDebug] crop summary")
      console.log("targetAspectRatio", TARGET_ASPECT_RATIO)
      console.log("source", {
        width: sourceWidth,
        height: sourceHeight,
        aspectRatio: sourceRatio,
      })
      console.log("crop", {
        width: Math.round(cropWidth),
        height: Math.round(cropHeight),
      })
      console.log("outputCanvas", {
        width,
        height,
        aspectRatio: width / height,
      })
      console.groupEnd()

      cropDebugLoggedRef.current = true
    }

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

      context.drawImage(
        video,
        sx,
        sy,
        sWidth,
        sHeight,
        0,
        0,
        canvas.width,
        canvas.height
      )

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

      canvasStream.getVideoTracks().forEach((track) => {
        recordingStream.addTrack(track)
      })

      streamRef.current.getAudioTracks().forEach((track) => {
        recordingStream.addTrack(track)
      })

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
        const file = new File([blob], `recorded-${timestamp}.webm`, {
          type: mimeType,
        })

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
          <div className="text-[64px] font-black leading-none text-primary-100">
            {remainingSeconds}
          </div>
        ) : (
          <h1
            className="text-[28px] font-medium leading-tight"
            style={{ wordBreak: "keep-all" }}
          >
            촬영할 대상을
            <br />
            <span className="text-primary-100">사각형 안</span>에 맞춰주세요
          </h1>
        )}
      </section>

      <section className="relative mt-4 aspect-[3/4] w-full shrink-0 overflow-hidden rounded-[15px] bg-[#1f1f1f]">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="h-full w-full object-cover"
        />

        <canvas ref={canvasRef} className="hidden" />

        <div className="pointer-events-none absolute inset-0 flex items-center justify-center px-16 py-24">
          <div className="h-full w-full rounded-[12px] border-[6px] border-[#ef4444]" />
        </div>
      </section>

      {errorMessage ? (
        <p className="mt-4 text-center text-sm text-red-400">{errorMessage}</p>
      ) : null}

      {!isRecording && rearCameraOptions.length > 1 ? (
        <section className="mt-3 flex items-center justify-center">
          <button
            type="button"
            onClick={handleSwitchRearCamera}
            disabled={!isReady}
            className="rounded-full border border-white/40 px-4 py-2 text-sm text-white disabled:opacity-40"
          >
            렌즈 전환
          </button>
        </section>
      ) : null}

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