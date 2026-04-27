import { useState } from "react"
import BottomTab from "@/components/common/BottomTab"
import InputBar from "@/components/common/InputBar"
import CharacterListen from "@/assets/character/CharacterListen.png"
import CharacterDdabong from "@/assets/character/CharacterDdabong.png"
import Record from "@/features/home/components/Record"

function HomePage() {
  const [isTyping, setIsTyping] = useState(false)
  const [isRecording, setIsRecording] = useState(false)

  const isActive = isTyping || isRecording

  return (
    <main className="relative flex min-h-screen justify-center bg-surface-50">
      <div className="min-h-screen w-full max-w-md px-5 py-6 pb-60">
        {/* 상단 영역 */}
        <section className="flex justify-center py-10">
          <h1 className="text-center text-2xl font-medium text-accent-500" style={{ wordBreak: "keep-all" }}>
            오늘 새로 공유해주실 이야기가 있나요?
          </h1>
        </section>

        {/* 캐릭터 영역 */}
        <section className="flex justify-center">
          <img
            src={isActive ? CharacterListen : CharacterDdabong}
            alt="똑디 캐릭터"
            className="object-contain"
          />
        </section>

        {/* 음성 입력 영역 */}
        {!isTyping && (
          <section className="mt-5 flex justify-center">
            <Record onToggle={setIsRecording} />
          </section>
        )}
      </div>

      {/* 입력 영역 */}
      <section className="fixed bottom-20 left-1/2 z-20 w-full max-w-md -translate-x-1/2">
        <InputBar onTyping={setIsTyping} disabled={isRecording} />
      </section>

      <BottomTab />
    </main>
  )
}

export default HomePage