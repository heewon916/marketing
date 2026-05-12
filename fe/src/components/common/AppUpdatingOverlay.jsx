import { useEffect, useState } from 'react'
import { subscribeAppUpdating } from '@/lib/PwaUpdate'

export default function AppUpdatingOverlay() {
  const [isUpdating, setIsUpdating] = useState(false)

  useEffect(() => {
    return subscribeAppUpdating(setIsUpdating)
  }, [])

  if (!isUpdating) {
    return null
  }

  return (
    <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-[#101820]/88 text-white">
      <div className="mb-4 h-10 w-10 animate-spin rounded-full border-4 border-white/30 border-t-white" />
      <p className="text-base font-semibold">앱을 업데이트하고 있어요</p>
      <p className="mt-2 text-sm text-white/80">잠시만 기다려 주세요. 곧 새 버전으로 전환됩니다.</p>
    </div>
  )
}
