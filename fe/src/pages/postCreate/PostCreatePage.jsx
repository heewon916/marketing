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
import CharacterListen from "@/assets/character/CharacterListen.mp4"
import CharacterCamera from "@/assets/character/CharacterCamera.mp4"
import PostCreateLeaveHomeModal from "@/features/postCreate/components/PostCreateLeaveHomeModal"
import { requestVideoUpload } from "@/features/postCreate/api/VideoApi"
import { requestDraftPost, requestEditDraftCaption } from "@/features/postCreate/api/PostApi"
import { requestPublishStart, requestPublishStatus } from "@/features/postCreate/api/PublishApi"
import { showToast } from '@/utils/toast';
import { speak, stopTTS } from '@/utils/tts'
import {
  questionStepTTS,
  publishResultSuccessTTS,
  publishResultFailTTS,
  homeTTS
} from "@/assets/TTS"

const POST_QUESTION_TITLE = "이 이야기를 바탕으로 메뉴 홍보 게시글을 써볼까요?"
const CAMERA_QUESTION_FALLBACK_TITLE = "치킨의 바삭한 날개와 촉촉한 속을 대비되게 촬영하세요."
const POST_LOADING_TITLE = "멋진 게시물을 만드는 중..."
const EXTRACT_LOADING_FALLBACK_TITLE = "영상에서 가게의 멋진 사진을 가져오는 중..."
const PUBLISH_LOADING_TITLE = "인스타그램에 발행하고 있어요"
const PUBLISH_SUCCESS_TITLE = "발행 성공! 고생하셨습니다."
const PUBLISH_FAIL_TITLE = "발행 실패!"

const FIXED_AUDIO_STEPS = new Set([
  POST_CREATE_STEP.POST_QUESTION,
  POST_CREATE_STEP.POST_LOADING,
  POST_CREATE_STEP.EXTRACT_LOADING,
  POST_CREATE_STEP.PUBLISH_LOADING,
  POST_CREATE_STEP.PUBLISH_SUCCESS,
  POST_CREATE_STEP.PUBLISH_FAIL,
])

function getFixedAudioFallbackText(step) {
  if (step === POST_CREATE_STEP.POST_QUESTION) {
    return POST_QUESTION_TITLE
  }

  if (step === POST_CREATE_STEP.POST_LOADING) {
    return POST_LOADING_TITLE
  }

  if (step === POST_CREATE_STEP.EXTRACT_LOADING) {
    return EXTRACT_LOADING_FALLBACK_TITLE
  }

  if (step === POST_CREATE_STEP.PUBLISH_LOADING) {
    return PUBLISH_LOADING_TITLE
  }

  if (step === POST_CREATE_STEP.PUBLISH_SUCCESS) {
    return PUBLISH_SUCCESS_TITLE
  }

  if (step === POST_CREATE_STEP.PUBLISH_FAIL) {
    return PUBLISH_FAIL_TITLE
  }

  return POST_QUESTION_TITLE
}

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
    if (step === POST_CREATE_STEP.PUBLISH_LOADING) {
      let isActive = true
      let intervalId = null

      const startPublishAndPoll = async () => {
        try {
          console.log("[PostCreate] publish:start request", { sessionId })
          await requestPublishStart(sessionId)
          console.log("[PostCreate] publish:start success", { sessionId })

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
          console.error("[PostCreate] publish:start failed", error)
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

  useEffect(() => {
    if (step === POST_CREATE_STEP.CAMERA_QUESTION) {
      const cameraQuestionText = guideText?.trim() || CAMERA_QUESTION_FALLBACK_TITLE
      void speak(cameraQuestionText, {
        source: "tts",
      })
      return
    }

    // 로딩 단계에서는 TTS를 비활성화
    if (
      step === POST_CREATE_STEP.POST_LOADING ||
      step === POST_CREATE_STEP.EXTRACT_LOADING ||
      step === POST_CREATE_STEP.PUBLISH_LOADING
    ) {
      stopTTS();
      return;
    }

    if (FIXED_AUDIO_STEPS.has(step)) {
      let audioSrc = homeTTS;
      if (step === POST_CREATE_STEP.POST_QUESTION) {
        audioSrc = questionStepTTS;
      } else if (step === POST_CREATE_STEP.PUBLISH_SUCCESS) {
        audioSrc = publishResultSuccessTTS;
      } else if (step === POST_CREATE_STEP.PUBLISH_FAIL) {
        audioSrc = publishResultFailTTS;
      }
      void speak(getFixedAudioFallbackText(step), {
        source: "file",
        audioSrc,
        fallbackToTTS: true,
      });
      return;
    }

    stopTTS()
  }, [guideText, step])

  useEffect(() => {
    return () => {
      stopTTS()
    }
  }, [])

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
      const uploaded = await requestVideoUpload(videoFile, sessionId)

      const extractedFrames = Array.isArray(uploaded?.extracted_frames)
        ? uploaded.extracted_frames
        : []

      if (extractedFrames.length > 0) {
        setPhotos(
          extractedFrames.map((frame, index) => ({
            id: frame.image_id ?? `image-${index}`,
            url: frame.original_key ?? "",
            imageKey: frame.image_id ?? "",
          }))
        )
      }

      setStep(POST_CREATE_STEP.PHOTO_CONFIRM)
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
    console.log("[PostCreate] publish:clicked", { hasContent: post?.content !== undefined })

    if (post?.content !== undefined) {
      try {
        console.log("[PostCreate] caption:edit request", { sessionId })
        const updated = await requestEditDraftCaption(sessionId, post.content)
        console.log("[PostCreate] caption:edit success", { sessionId, updatedAt: updated.updatedAt })
        setGeneratedPost({
          ...(generatedPost ?? {}),
          ...post,
          content: updated.caption,
          updatedAt: updated.updatedAt,
        })
      } catch (error) {
        console.error("[PostCreate] caption:edit failed", error)
        showToast(error.message || "캡션 수정에 실패했습니다.", 'error')
        return
      }
    } else if (post) {
      console.log("[PostCreate] caption:edit skipped", { reason: "content is undefined" })
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
        title={POST_QUESTION_TITLE}
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
        title={POST_LOADING_TITLE}
        stepNum={stepNum}
      />
    )
  }

  if (step === POST_CREATE_STEP.CAMERA_QUESTION) {
    content = (
      <QuestionStep
        title={guideText?.trim() || CAMERA_QUESTION_FALLBACK_TITLE}
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
        title={PUBLISH_LOADING_TITLE}
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
