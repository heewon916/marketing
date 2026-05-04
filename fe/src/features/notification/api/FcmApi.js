import { getFcmToken } from "@/features/notification/lib/getFcmToken"

export async function registerFcmToken(options = {}) {
  try {
    const token = await getFcmToken(options)
    console.log("[FCM] 발급된 토큰:", token)
    return token || null
  } catch (e) {
    const isPermissionDenied = e?.name === "AbortError" && e?.message?.includes("permission denied")
    const isPushServiceError =
      e?.name === "AbortError" &&
      String(e?.message || "").toLowerCase().includes("push service error")

    console.warn("FCM 토큰 발급 실패:", e)
    console.warn("FCM 상세 정보:", {
      name: e?.name,
      code: e?.code,
      message: e?.message,
    })

    if (isPermissionDenied) {
      console.warn(
        "[FCM] Push 구독이 브라우저에서 거부되었습니다. Chrome 시크릿 모드에서는 Web Push가 지원되지 않거나, 사이트 알림/푸시 설정이 차단된 상태일 수 있습니다.",
      )
    }

    if (isPushServiceError) {
      console.warn(
        "[FCM] Chrome Push Service 상태 문제 가능성이 큽니다. 같은 코드가 Edge에서 동작하면 Firebase 값 문제는 아닙니다. Chrome 사이트 데이터/서비스워커/확장 프로그램 상태를 점검하세요.",
      )
    }

    return null
  }
}