import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import BottomTab from "@/components/common/BottomTab"
import InputBar from "@/components/common/InputBar"
import Character from "@/components/common/Character"
import TitleText from "@/components/common/TitleText"
import { registerFcmToken } from "@/features/notification/api/FcmApi"
import { requestCaptionGeneration } from "@/features/home/api/HomeApi"
import { usePostCreateStore } from "@/features/postCreate/store/postCreateStore"
import { POST_CREATE_STEP } from "@/features/postCreate/constants/postCreateStep"
import { showToast } from '@/utils/toast'
import { speak, stopTTS } from '@/utils/tts'
import homeGreetingAudio from "@/assets/TTS/home_tts.mp3"

const HOME_GREETING_TEXT = "오늘 새로 공유해주실 이야기가 있나요?"
const HOME_GREETING_AUDIO_SRC = homeGreetingAudio

function HomePage() {
  const [isTyping, setIsTyping] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [greetingText, setGreetingText] = useState(HOME_GREETING_TEXT)
  const navigate = useNavigate()
  const setStep = usePostCreateStore((state) => state.setStep)
  const setGenerationContext = usePostCreateStore((state) => state.setGenerationContext)

  // 홈페이지 진입 시 TTS 재생
  useEffect(() => {
    speak(HOME_GREETING_TEXT, {
      source: "file",
      audioSrc: HOME_GREETING_AUDIO_SRC,
      fallbackToTTS: true,
    })

    return () => {
      stopTTS()
    }
  }, [])

  const isActive = isTyping || isRecording

  const handleSubmitUtterance = async (utterance) => {
    const result = await requestCaptionGeneration(utterance)

    if (result.status === 'GENERAL_CHAT') {
      setGreetingText(result.caption)
      speak(result.caption)
      return
    }

    setGenerationContext({
      requestId: result.requestId,
      sessionId: result.sessionId,
      utterance,
      guideText: result.guideText,
      draftCaption: result.caption,
    })
    setStep(POST_CREATE_STEP.POST_QUESTION)
    navigate("/post-create")
  }

  return (
    <main className="relative flex h-dvh justify-center bg-surface-50">
      <div className="relative h-full w-full max-w-md px-5 py-6 pb-60">

        {/* 상단 여백 */}
        <section className="flex justify-center pt-7">
          
        </section>

        {/* 상단 글 영역 */}
        <section className="flex h-40 items-center justify-center">
          <TitleText text={greetingText} />
        </section>

        {/* 캐릭터 영역 */}
        <section className="flex justify-center items-end h-[45vh] min-h-[120px]">
          <Character
            type={isActive ? "listen" : "ddabong"}
            className="h-full max-h-[40vh] max-w-[80vw] w-auto"
          />
        </section>

      </div>

      {/* 텍스트 입력 영역 */}
      <section className="fixed bottom-20 left-1/2 z-20 w-full max-w-md -translate-x-1/2">
        <InputBar
          onTyping={setIsTyping}
          onRecordingChange={setIsRecording}
          onSubmit={handleSubmitUtterance}
        />
      </section>

      <BottomTab />
    </main>
  )
}

export default HomePage