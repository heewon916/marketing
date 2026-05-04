console.log("[SW] firebase-messaging-sw.js 로드 시작")

importScripts("https://www.gstatic.com/firebasejs/12.12.1/firebase-app-compat.js")
importScripts("https://www.gstatic.com/firebasejs/12.12.1/firebase-messaging-compat.js")

console.log("[SW] Firebase scripts importScripts 완료")

firebase.initializeApp({
  apiKey: "AIzaSyCgh1fMhj2CDKQJModmqYuZxF1t5S8t8IA",
  authDomain: "marketing-assist-for-ceo.firebaseapp.com",
  projectId: "marketing-assist-for-ceo",
  storageBucket: "marketing-assist-for-ceo.firebasestorage.app",
  messagingSenderId: "974751746488",
  appId: "1:974751746488:web:8ff936ccb240430a1b274d",
  measurementId: "G-V7KLPDC2K9"
})

console.log("[SW] Firebase 앱 초기화 완료")

const messaging = firebase.messaging()
console.log("[SW] messaging 인스턴스 생성 완료:", messaging)

self.addEventListener("activate", (event) => {
  console.log("[SW] activate 이벤트")
  event.waitUntil(self.clients.claim())
})

self.addEventListener("message", (event) => {
  console.log("[SW] message 이벤트 수신:", event.data)
  if (event.data?.type === "SKIP_WAITING") {
    console.log("[SW] SKIP_WAITING 실행")
    self.skipWaiting()
  }
})

messaging.onBackgroundMessage((payload) => {
  console.log("[SW] onBackgroundMessage 수신 - payload:", JSON.stringify(payload))
  console.log("[SW] notification:", payload.notification)
  console.log("[SW] data:", payload.data)
  const title = payload.notification?.title || payload.data?.title || "alarm"
  const body = payload.notification?.body || payload.data?.body || ""
  const url = payload.data?.url || payload.fcmOptions?.link || "/"

  event?.waitUntil?.(
    self.registration.showNotification(title, {
      body,
      icon: "/pwa-192x192.png",
      badge: "/pwa-192x192.png",
      data: {
        ...payload.data,
        url,
      },
    }),
  )
  console.log("[SW] showNotification 호출 완료")
})

self.addEventListener("notificationclick", (event) => {
  console.log("[SW] notificationclick 이벤트:", event)
  console.log("[SW] notification.data:", event.notification.data)
  event.notification.close()

  const url = event.notification.data?.url || "/"
  console.log("[SW] 열 URL:", url)

  event.waitUntil((async () => {
    const normalizedUrl = new URL(url, self.location.origin).href
    const clientList = await clients.matchAll({ type: "window", includeUncontrolled: true })

    for (const client of clientList) {
      if (client.url === normalizedUrl && "focus" in client) {
        await client.focus()
        return
      }
    }

    await clients.openWindow(normalizedUrl)
  })())
})