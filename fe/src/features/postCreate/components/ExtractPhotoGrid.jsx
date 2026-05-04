import { useEffect, useState } from "react"

const TOTAL_CARDS = 3

function PhotoCard({ state, src }) {
  if (state === "loaded") {
    return (
      <div className="aspect-square w-full overflow-hidden rounded-2xl bg-gray-200">
        {src ? (
          <img src={src} alt="추출된 사진" className="h-full w-full object-cover" />
        ) : (
          <div className="h-full w-full bg-gradient-to-br from-amber-100 to-orange-200" />
        )}
      </div>
    )
  }

  if (state === "loading") {
    return (
      <div className="relative aspect-square w-full overflow-hidden rounded-2xl bg-gray-200">
        <div className="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/70 to-transparent" />
      </div>
    )
  }

  return <div className="flex aspect-square w-full items-center justify-center rounded-2xl bg-gray-100" />
}

function ExtractPhotoGrid({ photos = [] }) {
  const [animatedCount, setAnimatedCount] = useState(0)

  useEffect(() => {
    if (animatedCount >= TOTAL_CARDS) return
    const timer = setTimeout(() => setAnimatedCount((c) => c + 1), 2500)
    return () => clearTimeout(timer)
  }, [animatedCount])

  return (
    <section className="grid grid-cols-3 gap-3 pb-6">
      {Array.from({ length: TOTAL_CARDS }).map((_, i) => {
        const src = photos[i]?.url
        if (i < animatedCount) {
          return <PhotoCard key={i} state="loaded" src={src} />
        }
        if (i === animatedCount) {
          return <PhotoCard key={i} state="loading" />
        }
        return <PhotoCard key={i} state="waiting" />
      })}
    </section>
  )
}

export default ExtractPhotoGrid