import { api } from "@/lib/Axios";

let currentAudio = null;

export async function speak(text, options = {}) {
  if (!text) return;

  // 말하던게 있으면 중단하고 다음 말
  stopTTS();

  try {
    const { volume = 1, onEnd, onError } = options;

    const response = await api.post("/api/v1/contents/tts", { text }, {
      responseType: "blob",
    });

    const audioBlob = response.data;
    const audioUrl = URL.createObjectURL(audioBlob);

    const audio = new Audio(audioUrl);
    audio.volume = volume;

    audio.addEventListener("ended", () => {
      URL.revokeObjectURL(audioUrl);
      onEnd?.();
    });

    audio.addEventListener("error", (e) => {
      URL.revokeObjectURL(audioUrl);
      onError?.(new Error(`Audio playback error: ${e.message}`));
    });

    currentAudio = audio;
    await audio.play();
  } catch (error) {
    options.onError?.(error);
  }
}

export function stopTTS() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
}
