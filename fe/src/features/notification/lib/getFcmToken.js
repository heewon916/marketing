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
  if (typeof window === "undefined" || !window.isSecureContext) {
    return null;
  }

  if (!("Notification" in window)) {
    return null;
  }

  if (!("serviceWorker" in navigator)) {
    return null;
  }

  let permission = Notification.permission;

  if (permission === "default" && requestPermission) {
    permission = await Notification.requestPermission();
  }

  if (permission !== "granted") {
    return null;
  }

  const messaging = await getFirebaseMessaging();
  if (!messaging) {
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
      const token = await getToken(messaging, attempt.options)

      if (!token) {
        continue
      }

      return token
    } catch (error) {
      lastError = error
    }
  }

  const isPushServiceError =
    lastError?.name === "AbortError" &&
    String(lastError?.message || "").toLowerCase().includes("push service error")

  if (isPushServiceError) {
    await resetFcmServiceWorkerState()

    const retryRegistration = await navigator.serviceWorker.register(FCM_SW_URL, { scope: "/" })
    await waitForActiveServiceWorker(retryRegistration)

    try {
      const retryToken = await getToken(messaging, {
        ...(vapidKey ? { vapidKey } : {}),
        serviceWorkerRegistration: retryRegistration,
      })

      if (retryToken) {
        return retryToken
      }
    } catch (retryError) {
      lastError = retryError
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
