import { getFcmToken } from "@/features/notification/lib/getFcmToken"
import { api } from "@/lib/Axios"

async function sendTokenToBackend(token) {
  try {
    const response = await api.post("/api/v1/users/me/fcm-token", {
      token,
      platform: "WEB",
    })

    return response.data
  } catch (error) {
    console.error("[FCM] 백엔드 토큰 전송 실패:", error)
    console.log("[FCM] 요청 정보:", {
      url: error.config?.url,
      method: error.config?.method,
      headers: error.config?.headers,
      body: error.config?.data,
      status: error.response?.status,
      responseData: error.response?.data,
    })
    throw error
  }
}

export async function registerFcmToken(options = {}) {
  console.log("hi")
  try {
    const token = await getFcmToken(options)
    if (token) {
      console.log("[FCM] 발급된 토큰:", token)
      await sendTokenToBackend(token)
    }
    return token || null
  } catch(error) {
    console.log(error)
    return null
  }
}