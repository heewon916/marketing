import { initializeApp } from "firebase/app"
import {
  getAnalytics,
  isSupported as isAnalyticsSupported,
} from "firebase/analytics"
import { getMessaging, isSupported, onMessage } from "firebase/messaging"

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
}

export const firebaseApp = initializeApp(firebaseConfig)

isAnalyticsSupported().then((supported) => {
  if (supported) {
    getAnalytics(firebaseApp)
  }
})

export const getFirebaseMessaging = async () => {
  const supported = await isSupported()
  if (!supported) return null

  return getMessaging(firebaseApp)
}

let unsubscribeForegroundMessage = null

function getNotificationPayload(payload) {
  const title = payload.notification?.title || payload.data?.title || "알림"
  const body = payload.notification?.body || payload.data?.body || ""
  const url =
    payload.data?.web_url ||
    payload.data?.url ||
    payload.fcmOptions?.link ||
    "/"

  return { title, body, url }
}

export async function initForegroundMessage() {
  if (unsubscribeForegroundMessage) return

  const messaging = await getFirebaseMessaging()
  if (!messaging) return

  unsubscribeForegroundMessage = onMessage(messaging, async (payload) => {
    console.log("[FCM] foreground payload:", payload)

    if (Notification.permission !== "granted") {
      console.warn("[FCM] 알림 권한 없음:", Notification.permission)
      return
    }

    if (!("serviceWorker" in navigator)) {
      console.warn("[FCM] serviceWorker 미지원")
      return
    }

    const { title, body, url } = getNotificationPayload(payload)

    try {
      const registration = await navigator.serviceWorker.ready
      const swUrl = registration.active?.scriptURL || "unknown"
      console.log("[FCM] active SW:", swUrl)

      await registration.showNotification(title, {
        body,
        icon: "/icon_192.png",
        badge: "/icon_192.png",
        data: { url },
        requireInteraction: true,
        tag: `fcm-foreground-${Date.now()}`,
      })

      console.log("[FCM] notification displayed")
    } catch (error) {
      console.error("[FCM] showNotification 실패:", error)
    }
  })
}