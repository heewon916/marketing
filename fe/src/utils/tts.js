import { api } from "@/lib/Axios";

let currentAudio = null;
let currentObjectUrl = null;
const TTS_MUTE_STORAGE_KEY = "tts-muted";

function getInitialMutedState() {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(TTS_MUTE_STORAGE_KEY) === "true";
}

let isMuted = getInitialMutedState();

function normalizeVolume(volume) {
  const numericVolume = Number(volume);

  if (Number.isNaN(numericVolume)) {
    return 1;
  }

  return Math.min(1, Math.max(0, numericVolume));
}

function cleanupObjectUrl() {
  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl);
    currentObjectUrl = null;
  }
}

function attachAudioEvents(audio, { onEnd, onError }) {
  audio.addEventListener("ended", () => {
    cleanupObjectUrl();
    currentAudio = null;
    onEnd?.();
  });

  audio.addEventListener("error", () => {
    cleanupObjectUrl();
    currentAudio = null;
    onError?.(new Error("Audio playback error"));
  });
}

export async function speak(text, options = {}) {
  if (isMuted) {
    return;
  }

  // 말하던게 있으면 중단하고 다음 말
  stopTTS();

  try {
    const {
      volume = 1,
      onEnd,
      onError,
      source = "tts",
      audioSrc = "",
      fallbackToTTS = true,
    } = options;
    const resolvedVolume = normalizeVolume(volume);

    const shouldPlayFile = source === "file" && audioSrc;

    if (shouldPlayFile) {
      const audio = new Audio(audioSrc);
      audio.volume = resolvedVolume;
      attachAudioEvents(audio, { onEnd, onError });
      currentAudio = audio;
      await audio.play();
      return;
    }

    if (!text) {
      return;
    }

    console.log("[TTS] request", {
      endpoint: "/api/v1/contents/tts",
      text,
      textLength: text.length,
    });

    const response = await api.post(
      "/api/v1/contents/tts",
      { text },
      {
        responseType: "blob",
      },
    );

    console.log("[TTS] response", {
      endpoint: "/api/v1/contents/tts",
      status: response.status,
      size: response.data?.size,
      type: response.data?.type,
    });

    const audioBlob = response.data;
    const audioUrl = URL.createObjectURL(audioBlob);

    const audio = new Audio(audioUrl);
    audio.volume = resolvedVolume;
    currentObjectUrl = audioUrl;
    attachAudioEvents(audio, { onEnd, onError });
    currentAudio = audio;
    await audio.play();
  } catch (error) {
    console.error("[TTS] request failed", {
      endpoint: "/api/v1/contents/tts",
      message: error?.message,
      status: error?.response?.status,
    });

    if (error?.name === "AbortError") {
      return;
    }

    if (options.source === "file" && options.fallbackToTTS !== false && text) {
      try {
        await speak(text, { ...options, source: "tts" });
        return;
      } catch {
        // no-op
      }
    }

    options.onError?.(error);
  }
}

export function stopTTS() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }

  cleanupObjectUrl();
}

export function getTTSMuted() {
  return isMuted;
}

export function setTTSMuted(muted) {
  isMuted = Boolean(muted);

  if (typeof window !== "undefined") {
    localStorage.setItem(TTS_MUTE_STORAGE_KEY, String(isMuted));
  }

  if (isMuted) {
    stopTTS();
  }

  return isMuted;
}

export function toggleTTSMuted() {
  return setTTSMuted(!isMuted);
}
