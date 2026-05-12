import { create } from "zustand"
import { POST_CREATE_STEP } from "@/features/postCreate/constants/postCreateStep"

export const usePostCreateStore = create((set) => ({
  step: POST_CREATE_STEP.POST_QUESTION,

  requestId: "",
  sessionId: "",
  utterance: "",
  guideText: "",
  draftCaption: "",

  postAnswer: "",
  cameraAnswer: "",

  photos: [],
  generatedPost: null,

  setStep: (step) => set({ step }),

  setGenerationContext: ({ requestId = "", sessionId = "", utterance = "", guideText = "", draftCaption = "" }) =>
    set({ requestId, sessionId, utterance, guideText, draftCaption }),

  setPostAnswer: (postAnswer) => set({ postAnswer }),
  setCameraAnswer: (cameraAnswer) => set({ cameraAnswer }),

  setPhotos: (photos) => set({ photos }),
  setGeneratedPost: (generatedPost) => set({ generatedPost }),

  resetPostCreate: () =>
    set({
      step: POST_CREATE_STEP.POST_QUESTION,
      requestId: "",
      sessionId: "",
      utterance: "",
      guideText: "",
      draftCaption: "",
      postAnswer: "",
      cameraAnswer: "",
      photos: [],
      generatedPost: null,
    }),
}))