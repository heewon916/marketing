import { initializeApp } from "firebase/app"
import { getAnalytics } from "firebase/analytics";
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
export const firebaseanalytics = getAnalytics(firebaseApp);

export const getFirebaseMessaging = async () => {
  const supported = await isSupported()
  if (!supported) return null

  return getMessaging(firebaseApp)
}

// 웹이 포그라운드(켜진 상태)일 때도 백그라운드와 동일한 OS 알림 표시
export async function initForegroundMessage() {
  const messaging = await getFirebaseMessaging()
  if (!messaging) return

  onMessage(messaging, async (payload) => {
    const title = payload.notification?.title || payload.data?.title || "알림"
    const body = payload.notification?.body || payload.data?.body || ""
    const url = payload.data?.url || payload.fcmOptions?.link || "/"

    const registration = await navigator.serviceWorker.ready
    await registration.showNotification(title, {
      body,
      icon: "/pwa-192x192.png",
      badge: "/pwa-192x192.png",
      data: { url },
    })
  })
}