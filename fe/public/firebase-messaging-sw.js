importScripts("https://www.gstatic.com/firebasejs/12.12.1/firebase-app-compat.js")
importScripts("https://www.gstatic.com/firebasejs/12.12.1/firebase-messaging-compat.js")

firebase.initializeApp({
  apiKey: "AIzaSyCgh1fMhj2CDKQJModmqYuZxF1t5S8t8IA",
  authDomain: "marketing-assist-for-ceo.firebaseapp.com",
  projectId: "marketing-assist-for-ceo",
  storageBucket: "marketing-assist-for-ceo.firebasestorage.app",
  messagingSenderId: "974751746488",
  appId: "1:974751746488:web:8ff936ccb240430a1b274d",
  measurementId: "G-V7KLPDC2K9"
})

const messaging = firebase.messaging()
let lastNotificationKey = null

function buildNotificationPayload(payload) {
  const title = payload.notification?.title || payload.data?.title || "알림"
  const body = payload.notification?.body || payload.data?.body || ""
  const url = payload.data?.web_url || payload.data?.url || payload.fcmOptions?.link || "/"
  const key = `${title}::${body}::${url}`

  return { title, body, url, key }
}

function shouldSkipDuplicate(key) {
  if (!key) return false
  if (lastNotificationKey === key) return true
  lastNotificationKey = key
  setTimeout(() => {
    if (lastNotificationKey === key) {
      lastNotificationKey = null
    }
  }, 2000)
  return false
}

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") {
    self.skipWaiting()
  }
})

messaging.onBackgroundMessage((payload) => {
  const { title, body, url, key } = buildNotificationPayload(payload)
  if (shouldSkipDuplicate(key)) return

  return self.registration.showNotification(title, {
    body,
      icon: "/icon_192.png",
      badge: "/icon_192.png",
    requireInteraction: true,
    tag: `fcm-${Date.now()}`,
    data: {
      ...payload.data,
      url,
    },
  })
})

self.addEventListener("notificationclick", (event) => {
  event.notification.close()

  const url = event.notification.data?.url || "/"
  const notifBody = event.notification.body || ""

  event.waitUntil((async () => {
    const normalizedUrl = new URL(url, self.location.origin).href
    const clientList = await clients.matchAll({ type: "window", includeUncontrolled: true })

    // 열려 있는 모든 탭에 body 전달 (저장용)
    for (const client of clientList) {
      client.postMessage({ type: "NOTIF_BODY_CLICKED", body: notifBody })
    }

    for (const client of clientList) {
      if (client.url === normalizedUrl && "focus" in client) {
        await client.focus()
        return
      }
    }

    // 열린 창이 없으면 URL에 notifBody 파라미터를 붙여서 새 창 열기
    const targetUrl = new URL(normalizedUrl)
    if (notifBody) targetUrl.searchParams.set("notifBody", notifBody)
    await clients.openWindow(targetUrl.href)
  })())
})