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
import { requestVideoUpload } from "@/features/postCreate/api/VideoApi"
import { requestDraftPost, requestEditDraftCaption } from "@/features/postCreate/api/PostApi"
import { requestPublishStart, requestPublishStatus } from "@/features/postCreate/api/PublishApi"
import { showToast } from '@/utils/toast';

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
  const sessionId = usePostCreateStore((state) => state.sessionId)

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
      let isActive = true
      let intervalId = null

      const startPublishAndPoll = async () => {
        try {
          await requestPublishStart(sessionId)

          if (!isActive) {
            return
          }

          intervalId = setInterval(async () => {
            try {
              const status = await requestPublishStatus(sessionId)

              if (!isActive) {
                return
              }

              const progress = String(status.publishProgress || "").toLowerCase()

              if (progress === "completed") {
                clearInterval(intervalId)
                const currentPost = usePostCreateStore.getState().generatedPost ?? {}
                setGeneratedPost({
                  ...currentPost,
                  contentId: status.contentId,
                  instagramMediaId: status.instagramMediaId,
                  instagramPermalink: status.instagramPermalink,
                })
                setStep(POST_CREATE_STEP.PUBLISH_SUCCESS)
                return
              }

              if (progress === "failed" || progress === "error") {
                clearInterval(intervalId)
                setStep(POST_CREATE_STEP.PUBLISH_FAIL)
              }
            } catch (error) {
              clearInterval(intervalId)
              if (isActive) {
                showToast(error.message || "발행 상태 확인에 실패했습니다.", 'error')
                setStep(POST_CREATE_STEP.PUBLISH_FAIL)
              }
            }
          }, 1000)
        } catch (error) {
          if (isActive) {
            showToast(error.message || "발행 시작에 실패했습니다.", 'error')
            setStep(POST_CREATE_STEP.PUBLISH_FAIL)
          }
        }
      }

      startPublishAndPoll()

      return () => {
        isActive = false
        if (intervalId) {
          clearInterval(intervalId)
        }
      }
    }
  }, [sessionId, setGeneratedPost, setPhotos, setStep, step])

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

  const handleVideoRecorded = async (videoFile) => {
    setStep(POST_CREATE_STEP.EXTRACT_LOADING)

    try {
      await requestVideoUpload(videoFile, sessionId)
    } catch (error) {
      showToast(error.message || "영상 업로드에 실패했습니다.", 'error')
      setStep(POST_CREATE_STEP.CAMERA_QUESTION)
    }
  }

  const handlePhotoConfirmNext = async (selectedPhotos = []) => {
    if (selectedPhotos.length > 0) {
      setPhotos(selectedPhotos)
    }

    try {
      const draft = await requestDraftPost(sessionId)

      if (draft.images.length > 0) {
        setPhotos(draft.images)
      }

      setGeneratedPost({
        content: draft.caption,
        status: draft.status,
        sessionId: draft.sessionId,
        instagramUsername: draft.instagramUsername,
        instagramProfileImageUrl: draft.instagramProfileImageUrl,
      })

      setStep(POST_CREATE_STEP.GENERATED_POST)
    } catch (error) {
      showToast(error.message || "임시 게시물을 불러오지 못했습니다.", 'error')
    }
  }

  const handlePublish = async (post) => {
    if (post?.content !== undefined) {
      try {
        const updated = await requestEditDraftCaption(sessionId, post.content)
        setGeneratedPost({
          ...(generatedPost ?? {}),
          ...post,
          content: updated.caption,
          updatedAt: updated.updatedAt,
        })
      } catch (error) {
        showToast(error.message || "캡션 수정에 실패했습니다.", 'error')
        return
      }
    } else if (post) {
      setGeneratedPost(post)
    }

    setStep(POST_CREATE_STEP.PUBLISH_LOADING)
  }

  const handlePreviewFromEdit = async (post) => {
    if (post?.content !== undefined) {
      try {
        const updated = await requestEditDraftCaption(sessionId, post.content)
        setGeneratedPost({
          ...(generatedPost ?? {}),
          ...post,
          content: updated.caption,
          updatedAt: updated.updatedAt,
        })
      } catch (error) {
        showToast(error.message || "캡션 수정에 실패했습니다.", 'error')
        return
      }
    } else if (post) {
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
        title={guideText?.trim() || "치킨의 바삭한 날개와 촉촉한 속을 대비되게 촬영하세요."}
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
        sessionId={sessionId}
        photos={photos}
        onNext={handlePhotoConfirmNext}
        onLeaveHomeConfirm={handleLeaveToHome}
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
        onViewInstagram={() => {
          const permalink = generatedPost?.instagramPermalink?.trim()
          if (permalink) {
            window.open(permalink, "_blank", "noopener,noreferrer")
            return
          }

          showToast("인스타그램 게시물 링크를 찾지 못했습니다.", 'error')
        }}
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