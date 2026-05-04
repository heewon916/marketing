import { deleteToken, getToken } from "firebase/messaging";
import { getFirebaseMessaging } from "@/lib/firebase";

const FCM_SW_URL = "/firebase-messaging-sw.js"

async function resetFcmServiceWorkerState() {
  const registrations = await navigator.serviceWorker.getRegistrations()

  for (const reg of registrations) {
    const isFcmSw = reg.active?.scriptURL?.includes(FCM_SW_URL)
      || reg.installing?.scriptURL?.includes(FCM_SW_URL)
      || reg.waiting?.scriptURL?.includes(FCM_SW_URL)

    if (!isFcmSw) continue

    try {
      const sub = await reg.pushManager.getSubscription()
      await sub?.unsubscribe()
    } catch (_) {
      // ignore unsubscribe failures
    }

    await reg.unregister()
    console.log("[getFcmToken] FCM SW unregister 완료:", reg.scope)
  }
}

async function waitForActiveServiceWorker(registration, timeoutMs = 10000) {
  if (registration.active) return registration

  const worker = registration.installing || registration.waiting
  if (!worker) {
    throw new Error("Service worker is not installing/waiting/active")
  }

  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error("Service worker activation timeout"))
    }, timeoutMs)

    const onStateChange = () => {
      if (worker.state === "activated") {
        clearTimeout(timer)
        worker.removeEventListener("statechange", onStateChange)
        resolve()
      } else if (worker.state === "redundant") {
        clearTimeout(timer)
        worker.removeEventListener("statechange", onStateChange)
        reject(new Error("Service worker became redundant before activation"))
      }
    }

    worker.addEventListener("statechange", onStateChange)
    onStateChange()
  })

  return registration
}

export async function getFcmToken({ requestPermission = false } = {}) {
  console.log("[getFcmToken] 시작")

  if (typeof window === "undefined" || !window.isSecureContext) {
    console.warn("[getFcmToken] 보안 컨텍스트(HTTPS/localhost) 아님 - 토큰 발급 스킵")
    return null;
  }

  if (!("Notification" in window)) {
    console.warn("[getFcmToken] Notification API 미지원")
    return null;
  }

  if (!("serviceWorker" in navigator)) {
    console.warn("[getFcmToken] Service Worker 미지원")
    return null;
  }

  let permission = Notification.permission;
  console.log("[getFcmToken] 현재 알림 권한:", permission)

  if (permission === "default" && requestPermission) {
    permission = await Notification.requestPermission();
    console.log("[getFcmToken] 알림 권한 요청 결과:", permission)
  }

  if (permission !== "granted") {
    console.warn("[getFcmToken] 알림 권한 미승인 - 토큰 발급 스킵")
    return null;
  }

  const messaging = await getFirebaseMessaging();
  console.log("[getFcmToken] messaging 인스턴스:", messaging)
  if (!messaging) {
    console.warn("[getFcmToken] messaging이 null - FCM 미지원 환경")
    return null;
  }

  const vapidKey = (
    import.meta.env.VITE_FIREBASE_VAPID_KEY ||
    import.meta.env.VITE_FCM_VAPID_KEY ||
    ""
  ).trim()

  // SW가 active 상태가 된 뒤에만 Push subscribe(getToken)를 호출한다.
  const registration = await navigator.serviceWorker.register(FCM_SW_URL, { scope: "/" })
  await waitForActiveServiceWorker(registration)
  console.log("[getFcmToken] FCM SW 등록 및 활성화 완료")

  const attemptList = [
    {
      label: "registration + vapidKey",
      options: vapidKey
        ? { vapidKey, serviceWorkerRegistration: registration }
        : { serviceWorkerRegistration: registration },
    },
    {
      label: "registration only",
      options: { serviceWorkerRegistration: registration },
    },
  ]

  let lastError = null

  for (const attempt of attemptList) {
    try {
      console.log(`[getFcmToken] getToken 시도: ${attempt.label}`)
      const token = await getToken(messaging, attempt.options)

      if (!token) {
        console.warn(`[getFcmToken] 토큰 비어있음: ${attempt.label}`)
        continue
      }

      console.log(`[getFcmToken] FCM 토큰 획득 성공: ${attempt.label}`)
      return token
    } catch (error) {
      lastError = error
      console.warn(`[getFcmToken] getToken 실패: ${attempt.label}`, error?.message)
    }
  }

  const isPushServiceError =
    lastError?.name === "AbortError" &&
    String(lastError?.message || "").toLowerCase().includes("push service error")

  if (isPushServiceError) {
    console.warn("[getFcmToken] push service error 감지 - SW/구독 정리 후 1회 재시도")

    await resetFcmServiceWorkerState()

    const retryRegistration = await navigator.serviceWorker.register(FCM_SW_URL, { scope: "/" })
    await waitForActiveServiceWorker(retryRegistration)

    try {
      const retryToken = await getToken(messaging, {
        ...(vapidKey ? { vapidKey } : {}),
        serviceWorkerRegistration: retryRegistration,
      })

      if (retryToken) {
        console.log("[getFcmToken] 재시도 토큰 획득 성공")
        return retryToken
      }
    } catch (retryError) {
      lastError = retryError
      console.warn("[getFcmToken] 재시도 실패:", retryError?.message)
    }
  }

  try {
    // 모든 시도가 실패하면 기존 토큰을 한번 정리해 다음 시도 성공률을 높임
    await deleteToken(messaging).catch(() => {})
    throw lastError || new Error("FCM token issuance failed")
  } catch (cleanupError) {
    throw lastError || cleanupError
  }
}
