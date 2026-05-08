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

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") {
    self.skipWaiting()
  }
})

messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title || payload.data?.title || "alarm"
  const body = payload.notification?.body || payload.data?.body || ""
  const url = payload.data.web_url || payload.data?.url || payload.fcmOptions?.link || "/"

  return self.registration.showNotification(title, {
    body,
    icon: "/pwa-192x192.png",
    badge: "/pwa-192x192.png",
    data: {
      ...payload.data,
      url,
    },
  })
})

self.addEventListener("notificationclick", (event) => {
  event.notification.close()

  const url = event.notification.data?.url || "/"

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