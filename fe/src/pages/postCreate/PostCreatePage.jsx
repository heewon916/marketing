import { useEffect } from "react"
import { usePostCreateStore } from "@/features/postCreate/store/postCreateStore"
import { POST_CREATE_STEP } from "@/features/postCreate/constants/postCreateStep"

import QuestionStep from "@/features/postCreate/steps/QuestionStep"
import LoadingStep from "@/features/postCreate/steps/LoadingStep"

import CameraStep from "@/features/postCreate/steps/CameraStep"
import ExtractLoadingStep from "@/features/postCreate/steps/ExtractLoadingStep"
import PhotoConfirmStep from "@/features/postCreate/steps/PhotoConfirmStep"
import GeneratedPostStep from "@/features/postCreate/steps/GeneratedPostStep"
import PublishResultStep from "@/features/postCreate/steps/PublishResultStep"
import { useNavigate } from "react-router-dom"
import CharacterListen from "@/assets/character/CharacterListen.png"
import CharacterCamera from "@/assets/character/CharacterCamera.png"
import coffeeTest1 from "@/assets/test/coffee_test1.jpg"
import coffeeTest2 from "@/assets/test/coffee_test2.jpg"
import coffeeTest3 from "@/assets/test/coffee_test3.jpg"

const STEP_NUM = {
  [POST_CREATE_STEP.POST_QUESTION]: 1,
  [POST_CREATE_STEP.POST_LOADING]: 1,
  [POST_CREATE_STEP.CAMERA_QUESTION]: 2,
  [POST_CREATE_STEP.CAMERA]: 2,
  [POST_CREATE_STEP.EXTRACT_LOADING]: 3,
  [POST_CREATE_STEP.PHOTO_CONFIRM]: 3,
  [POST_CREATE_STEP.GENERATED_POST]: 4,
  [POST_CREATE_STEP.PUBLISH_LOADING]: 5,
  [POST_CREATE_STEP.PUBLISH_SUCCESS]: 5,
  [POST_CREATE_STEP.PUBLISH_FAIL]: 5,
}

export default function PostCreatePage() {
  const navigate = useNavigate()
  const step = usePostCreateStore((state) => state.step)
  const stepNum = STEP_NUM[step] ?? 1

  const postAnswer = usePostCreateStore((state) => state.postAnswer)
  const cameraAnswer = usePostCreateStore((state) => state.cameraAnswer)

  const photos = usePostCreateStore((state) => state.photos)
  const generatedPost = usePostCreateStore((state) => state.generatedPost)

  const setStep = usePostCreateStore((state) => state.setStep)
  const setPostAnswer = usePostCreateStore((state) => state.setPostAnswer)
  const setCameraAnswer = usePostCreateStore((state) => state.setCameraAnswer)
  const setPhotos = usePostCreateStore((state) => state.setPhotos)
  const setGeneratedPost = usePostCreateStore((state) => state.setGeneratedPost)
  const resetPostCreate = usePostCreateStore((state) => state.resetPostCreate)

  useEffect(() => {
    if (step === POST_CREATE_STEP.POST_LOADING) {
      const timer = setTimeout(() => setStep(POST_CREATE_STEP.CAMERA_QUESTION), 1500)
      return () => clearTimeout(timer)
    }
    if (step === POST_CREATE_STEP.EXTRACT_LOADING) {
      const timer = setTimeout(() => {
        setPhotos([
          { id: 1, url: coffeeTest1 },
          { id: 2, url: coffeeTest2 },
          { id: 3, url: coffeeTest3 },
        ])
        setStep(POST_CREATE_STEP.PHOTO_CONFIRM)
      }, 9000)
      return () => clearTimeout(timer)
    }
    if (step === POST_CREATE_STEP.PUBLISH_LOADING) {
      const timer = setTimeout(() => {
        const isSuccess = true
        setStep(isSuccess ? POST_CREATE_STEP.PUBLISH_SUCCESS : POST_CREATE_STEP.PUBLISH_FAIL)
      }, 1500)
      return () => clearTimeout(timer)
    }
  }, [step])

  const handlePostQuestionNext = () => {
    setPostAnswer("예")
    setStep(POST_CREATE_STEP.POST_LOADING)
  }

  const handleCameraQuestionNext = () => {
    setCameraAnswer("예")
    setStep(POST_CREATE_STEP.CAMERA)
  }

  const handleVideoRecorded = (videoFile) => {
    setStep(POST_CREATE_STEP.EXTRACT_LOADING)
  }

  const handlePhotoConfirmNext = () => {
    setGeneratedPost({
      content: "오늘 새벽에도 어김없이 시장에 다녀왔습니다. 눈으로 직접 보고 손으로 만져봐야 직성이 풀리는 성격이라, 20년째 국산 쌀이랑 깨는 제 손으로만 골라옵니다.",
      hashtags: ["신메뉴", "맛집", "오늘추천"],
    })

    setStep(POST_CREATE_STEP.GENERATED_POST)
  }

  const handlePublish = () => {
    setStep(POST_CREATE_STEP.PUBLISH_LOADING)
  }

  const handleLeaveToHome = () => {
    resetPostCreate()
    navigate("/home")
  }

  if (step === POST_CREATE_STEP.POST_QUESTION) {
    return (
      <QuestionStep
        title="이 이야기를 바탕으로 메뉴 홍보 게시글을 써볼까요?"
        onNext={handlePostQuestionNext}
        onLeaveHomeConfirm={handleLeaveToHome}
        stepNum={stepNum}
        characterSrc={CharacterListen}
        characterAlt="듣고 있는 캐릭터"
      />
    )
  }

  if (step === POST_CREATE_STEP.POST_LOADING) {
    return (
      <LoadingStep
        title="멋진 게시물을 만드는 중..."
        stepNum={stepNum}
      />
    )
  }

  if (step === POST_CREATE_STEP.CAMERA_QUESTION) {
    return (
      <QuestionStep
        title="신메뉴 치즈라떼를 만드는 영상을 찍어볼까요?"
        onNext={handleCameraQuestionNext}
        onLeaveHomeConfirm={handleLeaveToHome}
        stepNum={stepNum}
        characterSrc={CharacterCamera}
        characterAlt="카메라를 든 캐릭터"
      />
    )
  }

  if (step === POST_CREATE_STEP.CAMERA) {
    return <CameraStep onRecorded={handleVideoRecorded} onClose={() => setStep(POST_CREATE_STEP.CAMERA_QUESTION)} stepNum={stepNum} />
  }

  if (step === POST_CREATE_STEP.EXTRACT_LOADING) {
    return <ExtractLoadingStep stepNum={stepNum} photos={photos} />
  }

  if (step === POST_CREATE_STEP.PHOTO_CONFIRM) {
    return (
      <PhotoConfirmStep
        photos={photos}
        onNext={handlePhotoConfirmNext}
        onRetake={() => setStep(POST_CREATE_STEP.CAMERA)}
        stepNum={stepNum}
      />
    )
  }

  if (step === POST_CREATE_STEP.GENERATED_POST) {
    return (
      <GeneratedPostStep
        post={generatedPost}
        photos={photos}
        onPublish={handlePublish}
        onExit={() => setStep(POST_CREATE_STEP.PHOTO_CONFIRM)}
        stepNum={stepNum}
      />
    )
  }

  if (step === POST_CREATE_STEP.PUBLISH_LOADING) {
    return (
      <LoadingStep
        title="인스타그램에 발행하고 있어요"
        stepNum={stepNum}
      />
    )
  }

  if (step === POST_CREATE_STEP.PUBLISH_SUCCESS) {
    return (
      <PublishResultStep
        type="success"
        stepNum={stepNum}
        onGoHome={() => { resetPostCreate(); navigate("/home") }}
        onViewInstagram={() => window.open("https://www.instagram.com", "_blank", "noopener,noreferrer")}
      />
    )
  }

  if (step === POST_CREATE_STEP.PUBLISH_FAIL) {
    return (
      <PublishResultStep
        type="fail"
        stepNum={stepNum}
        onGoHome={() => { resetPostCreate(); navigate("/home") }}
        onRetry={() => setStep(POST_CREATE_STEP.GENERATED_POST)}
      />
    )
  }

  return null
}