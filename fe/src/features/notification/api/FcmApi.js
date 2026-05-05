import { getFcmToken } from "@/features/notification/lib/getFcmToken"
import { api } from "@/lib/Axios"

async function sendTokenToBackend(token) {
  try {
    const response = await api.post("/api/v1/users/me/fcm-token", {
      deviceToken: token,
      platform: "WEB",
    })

    return response.data
  } catch (error) {
    console.error("[FCM] 백엔드 토큰 전송 실패:", error)
    throw error
  }
}

export async function registerFcmToken(options = {}) {
  try {
    const token = await getFcmToken(options)
    if (token) {
      console.log("[FCM] 발급된 토큰:", token)
      await sendTokenToBackend(token)
    }
    return token || null
  } catch {
    return null
  }
}