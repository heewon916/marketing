import { useEffect, useState } from "react"
import { usePostCreateStore } from "@/features/postCreate/store/postCreateStore"
import { POST_CREATE_STEP } from "@/features/postCreate/constants/postCreateStep"

import QuestionStep from "@/features/postCreate/steps/QuestionStep"
import LoadingStep from "@/features/postCreate/steps/LoadingStep"

import CameraStep from "@/features/postCreate/steps/CameraStep"
import ExtractLoadingStep from "@/features/postCreate/steps/ExtractLoadingStep"
import PhotoConfirmStep from "@/features/postCreate/steps/PhotoConfirmStep"
import GeneratedPostStep from "@/features/postCreate/steps/GeneratedPostStep"
import GeneratedPostEditStep from "@/features/postCreate/steps/GeneratedPostEditStep"
import PublishResultStep from "@/features/postCreate/steps/PublishResultStep"
import { useBlocker, useNavigate } from "react-router-dom"
import CharacterListen from "@/assets/character/CharacterListen.png"
import CharacterCamera from "@/assets/character/CharacterCamera.png"
import coffeeTest1 from "@/assets/test/coffee_test1.jpg"
import coffeeTest2 from "@/assets/test/coffee_test2.jpg"
import coffeeTest3 from "@/assets/test/coffee_test3.jpg"
import PostCreateLeaveHomeModal from "@/features/postCreate/components/PostCreateLeaveHomeModal"

const STEP_NUM = {
  [POST_CREATE_STEP.POST_QUESTION]: 1,
  [POST_CREATE_STEP.POST_LOADING]: 1,
  [POST_CREATE_STEP.CAMERA_QUESTION]: 2,
  [POST_CREATE_STEP.CAMERA]: 2,
  [POST_CREATE_STEP.EXTRACT_LOADING]: 3,
  [POST_CREATE_STEP.PHOTO_CONFIRM]: 3,
  [POST_CREATE_STEP.GENERATED_POST]: 4,
  [POST_CREATE_STEP.GENERATED_POST_EDIT]: 4,
  [POST_CREATE_STEP.PUBLISH_LOADING]: 5,
  [POST_CREATE_STEP.PUBLISH_SUCCESS]: 5,
  [POST_CREATE_STEP.PUBLISH_FAIL]: 5,
}

export default function PostCreatePage() {
  const navigate = useNavigate()
  const [isNavigationConfirmed, setIsNavigationConfirmed] = useState(false)
  const step = usePostCreateStore((state) => state.step)
  const stepNum = STEP_NUM[step] ?? 1

  const guideText = usePostCreateStore((state) => state.guideText)

  const photos = usePostCreateStore((state) => state.photos)
  const generatedPost = usePostCreateStore((state) => state.generatedPost)

  const setStep = usePostCreateStore((state) => state.setStep)
  const setPostAnswer = usePostCreateStore((state) => state.setPostAnswer)
  const setCameraAnswer = usePostCreateStore((state) => state.setCameraAnswer)
  const setPhotos = usePostCreateStore((state) => state.setPhotos)
  const setGeneratedPost = usePostCreateStore((state) => state.setGeneratedPost)
  const resetPostCreate = usePostCreateStore((state) => state.resetPostCreate)

  const shouldGuardLeave =
    !isNavigationConfirmed &&
    step !== POST_CREATE_STEP.PUBLISH_SUCCESS &&
    step !== POST_CREATE_STEP.PUBLISH_FAIL

  const blocker = useBlocker(shouldGuardLeave)

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
  }, [setPhotos, setStep, step])

  const handleCancelLeave = () => {
    if (blocker.state === "blocked") {
      blocker.reset()
    }
  }

  const handleConfirmLeave = () => {
    setIsNavigationConfirmed(true)
    resetPostCreate()

    if (blocker.state === "blocked") {
      blocker.proceed()
      return
    }

    navigate("/home", { replace: true })
  }

  const handlePostQuestionNext = () => {
    setPostAnswer("예")
    setStep(POST_CREATE_STEP.POST_LOADING)
  }

  const handleCameraQuestionNext = () => {
    setCameraAnswer("예")
    setStep(POST_CREATE_STEP.CAMERA)
  }

  const handleVideoRecorded = () => {
    setStep(POST_CREATE_STEP.EXTRACT_LOADING)
  }

  const handlePhotoConfirmNext = () => {
    setGeneratedPost({
      content: `"다시 생각해보고 연락드릴게요" 케익 예약을 할까 말까 망설이다 끊게 되면 그만이기 마련. 간혹 오늘 오전처럼 설령 주문하지 않더라도 정중하게 양해를 구하는 전화를 다시 주는 분들도 계신데 과연 나는 저 나이때 이런 사려깊음이 있었던가? 돌이켜 보면서 한편으론, 어떤 일이든 어떤 관계든간에 그 성사 여부와는 별개로 서로간에 개운치 않는 기분을 남기지 않고 일을 일단락하는게 중요하지 않나 싶은. 성가시고 어렵기도 하지만 사람의 발전, 성숙이란 그런 데 있지 않나. 젊어서부터 체득한 분들.. 손님으로 모셔서 영광입니다..

가게의 케익은 초여름 산딸기를 지나, 지금은 #여름복숭아케익 그리고 올해 처음으로 #살구케익 도 시작하고 있습니다. 제철 과일 농작물들이 제 때 나오기가 점점 어려운 시대. 케익도 아껴 먹고, 소중한 지구 더 살뜰히 보살펴줘야겠습니다.

#수요휴무`
    })

    setStep(POST_CREATE_STEP.GENERATED_POST)
  }

  const handlePublish = (post) => {
    if (post) {
      setGeneratedPost(post)
    }
    setStep(POST_CREATE_STEP.PUBLISH_LOADING)
  }

  const handlePreviewFromEdit = (post) => {
    if (post) {
      setGeneratedPost(post)
    }
    setStep(POST_CREATE_STEP.GENERATED_POST)
  }

  const handleLeaveToHome = () => {
    navigate("/home")
  }

  let content = null

  if (step === POST_CREATE_STEP.POST_QUESTION) {
    content = (
      <QuestionStep
        title={guideText?.trim() || "이 이야기를 바탕으로 메뉴 홍보 게시글을 써볼까요?"}
        onNext={handlePostQuestionNext}
        onLeaveHomeConfirm={handleLeaveToHome}
        stepNum={stepNum}
        characterSrc={CharacterListen}
        characterAlt="듣고 있는 캐릭터"
      />
    )
  }

  if (step === POST_CREATE_STEP.POST_LOADING) {
    content = (
      <LoadingStep
        title="멋진 게시물을 만드는 중..."
        stepNum={stepNum}
      />
    )
  }

  if (step === POST_CREATE_STEP.CAMERA_QUESTION) {
    content = (
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
    content = <CameraStep onRecorded={handleVideoRecorded} onClose={() => setStep(POST_CREATE_STEP.CAMERA_QUESTION)} stepNum={stepNum} />
  }

  if (step === POST_CREATE_STEP.EXTRACT_LOADING) {
    content = <ExtractLoadingStep stepNum={stepNum} photos={photos} />
  }

  if (step === POST_CREATE_STEP.PHOTO_CONFIRM) {
    content = (
      <PhotoConfirmStep
        photos={photos}
        onNext={handlePhotoConfirmNext}
        onRetake={() => setStep(POST_CREATE_STEP.CAMERA)}
        stepNum={stepNum}
      />
    )
  }

  if (step === POST_CREATE_STEP.GENERATED_POST) {
    content = (
      <GeneratedPostStep
        post={generatedPost}
        photos={photos}
        onEdit={() => setStep(POST_CREATE_STEP.GENERATED_POST_EDIT)}
        onPublish={handlePublish}
        stepNum={stepNum}
      />
    )
  }

  if (step === POST_CREATE_STEP.GENERATED_POST_EDIT) {
    content = (
      <GeneratedPostEditStep
        post={generatedPost}
        photos={photos}
        onPublish={handlePublish}
        onExit={handlePreviewFromEdit}
        stepNum={stepNum}
      />
    )
  }

  if (step === POST_CREATE_STEP.PUBLISH_LOADING) {
    content = (
      <LoadingStep
        title="인스타그램에 발행하고 있어요"
        stepNum={stepNum}
      />
    )
  }

  if (step === POST_CREATE_STEP.PUBLISH_SUCCESS) {
    content = (
      <PublishResultStep
        type="success"
        stepNum={stepNum}
        onGoHome={() => { resetPostCreate(); navigate("/home") }}
        onViewInstagram={() => window.open("https://www.instagram.com", "_blank", "noopener,noreferrer")}
      />
    )
  }

  if (step === POST_CREATE_STEP.PUBLISH_FAIL) {
    content = (
      <PublishResultStep
        type="fail"
        stepNum={stepNum}
        onGoHome={() => { resetPostCreate(); navigate("/home") }}
        onRetry={() => setStep(POST_CREATE_STEP.GENERATED_POST_EDIT)}
      />
    )
  }

  return (
    <>
      {content}

      <PostCreateLeaveHomeModal
        isOpen={blocker.state === "blocked"}
        onClose={handleCancelLeave}
        onCancel={handleCancelLeave}
        onConfirm={handleConfirmLeave}
      />
    </>
  )
}