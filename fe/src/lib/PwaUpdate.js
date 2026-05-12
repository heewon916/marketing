import { registerSW } from 'virtual:pwa-register'

const listeners = new Set()
let isUpdating = false

const notify = () => {
  listeners.forEach((listener) => listener(isUpdating))
}

const startUpdateFlow = async () => {
  if (isUpdating) {
    return
  }

  isUpdating = true
  notify()

  try {
    await updateSW(true)
  } catch (error) {
    console.error('[PWA] Failed to apply service worker update:', error)
    window.location.reload()
  }
}

// Must export the function returned by registerSW so updateSW(true) can be called safely.
export const updateSW = registerSW({
  immediate: true,
  onNeedRefresh() {
    void startUpdateFlow()
  },
})

export const subscribeAppUpdating = (listener) => {
  listeners.add(listener)
  listener(isUpdating)

  return () => {
    listeners.delete(listener)
  }
}
