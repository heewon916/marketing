import { useState } from "react"
import { useNavigate } from "react-router-dom"
import BottomTab from "@/components/common/BottomTab"
import InputBar from "@/components/common/InputBar"
import Character from "@/components/common/Character"
import TitleText from "@/components/common/TitleText"

function HomePage() {
  const [isTyping, setIsTyping] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const navigate = useNavigate()

  const isActive = isTyping || isRecording

  return (
    <main className="relative flex h-dvh justify-center bg-surface-50">
      <div className="h-full w-full max-w-md px-5 py-6 pb-60">
        {/* 상단 여백 */}
        <section className="flex justify-center pt-2">
          <div className="h-7 w-80" />
        </section>

        {/* 상단 글 영역 */}
        <section className="flex h-40 items-center justify-center">
          <TitleText text="오늘 새로 공유해주실 이야기가 있나요?" />
        </section>

        {/* 캐릭터 영역 */}
        <section className="flex justify-center">
          <Character
            type={isActive ? "listen" : "ddabong"}
            className="max-h-[40vh]"
            onClick={() => navigate("/post-create")}
          />
        </section>

      </div>

      {/* 텍스트 입력 영역 */}
      <section className="fixed bottom-20 left-1/2 z-20 w-full max-w-md -translate-x-1/2">
        <InputBar
          onTyping={setIsTyping}
          onRecordingChange={setIsRecording}
        />
      </section>

      <BottomTab />
    </main>
  )
}

export default HomePage