import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import ToastContainer from '@/components/common/ToastContainer'

const PENDING_NOTIF_KEY = 'pendingNotifBody'

function App() {
  useEffect(() => {
    // URL 파라미터로 전달된 경우 (앱이 닫혀 있다가 알림 클릭 시 새 창 열림)
    const params = new URLSearchParams(window.location.search)
    const notifBody = params.get('notifBody')
    if (notifBody) {
      localStorage.setItem(PENDING_NOTIF_KEY, notifBody)
      params.delete('notifBody')
      const newSearch = params.toString()
      const newUrl = window.location.pathname + (newSearch ? `?${newSearch}` : '') + window.location.hash
      window.history.replaceState(null, '', newUrl)
    }

    // 앱이 열려 있는 상태에서 알림 클릭 시 SW postMessage로 전달
    const handleSwMessage = (event) => {
      if (event.data?.type === 'NOTIF_BODY_CLICKED' && event.data.body) {
        localStorage.setItem(PENDING_NOTIF_KEY, event.data.body)
      }
    }

    navigator.serviceWorker?.addEventListener('message', handleSwMessage)
    return () => {
      navigator.serviceWorker?.removeEventListener('message', handleSwMessage)
    }
  }, [])

  return (
    <div className="mx-auto w-full max-w-md bg-white">
      <Outlet />
      <ToastContainer />
    </div>
  )
}

export default App
