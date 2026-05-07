// 녹음 기능 컴포넌트, 현재 사용 안함(추후 개발을 위해 남겨둠)
import { useRef, useState } from "react"
import { TiMicrophone } from "react-icons/ti"


function Record({ onToggle }) {
  const [isRecording, setIsRecording] = useState(false)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" })
        const url = URL.createObjectURL(blob)
        const a = document.createElement("a")
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-")
        a.href = url
        a.download = `recording-${timestamp}.webm`
        a.click()
        URL.revokeObjectURL(url)

        stream.getTracks().forEach((track) => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      onToggle?.(true)
    } catch {
      alert("마이크 접근 권한이 필요합니다.")
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
    onToggle?.(false)
  }

  const handleClick = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  return (
    <div className="relative flex items-center justify-center">
      {/* 바깥 펄스 링 */}
      <span
        className={[
          "absolute rounded-full",
          isRecording
            ? "h-20 w-20 animate-ping bg-[#ff7a3d] opacity-20"
            : "h-20 w-20 bg-[#ff7a3d] opacity-10",
        ].join(" ")}
      />

      {/* 버튼 본체 */}
      <button
        type="button"
        aria-label={isRecording ? "녹음 중지" : "녹음 시작"}
        onClick={handleClick}
        className={[
          "relative z-10 flex h-20 w-20 items-center justify-center rounded-full shadow-[0_0_20px_rgba(255,122,61,0.4)] transition-colors duration-200",
          isRecording ? "bg-[#FFF3EC]" : "bg-white",
        ].join(" ")}
      >
        <TiMicrophone className="text-[#ff7a3d]" size={40} />
      </button>
    </div>
  )
}

export default Record
