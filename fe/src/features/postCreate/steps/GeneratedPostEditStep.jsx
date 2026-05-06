import { useEffect, useRef, useState } from "react"
import StepProgress from "@/components/common/StepProgress"
import Button from "@/components/common/Button"
import BottomTab from "@/components/common/BottomTab"
import GeneratedPostCarousel from "@/features/postCreate/components/GeneratedPostCarousel"
import GeneratedPostBody from "@/features/postCreate/components/GeneratedPostBody"

export default function GeneratedPostEditStep({ post, photos = [], onPublish, onExit, stepNum }) {
  const [editedContent, setEditedContent] = useState(post?.content ?? "")
  const [editedHashtags, setEditedHashtags] = useState(post?.hashtags ?? [])
  const [isBodyScrollable, setIsBodyScrollable] = useState(false)
  const [canScrollDown, setCanScrollDown] = useState(false)
  const [hasDelayPassed, setHasDelayPassed] = useState(false)
  const [hasUserScrolled, setHasUserScrolled] = useState(false)
  const contentSectionRef = useRef(null)

  const updateBodyScrollState = (el) => {
    if (!el) return
    const scrollable = el.scrollHeight > el.clientHeight
    const hasMoreBelow = scrollable && el.scrollTop + el.clientHeight < el.scrollHeight - 1
    setIsBodyScrollable(scrollable)
    setCanScrollDown(hasMoreBelow)
  }

  const handleBodyScroll = (e) => {
    const el = e.currentTarget
    if (el.scrollTop > 0) setHasUserScrolled(true)
    updateBodyScrollState(el)
  }

  const shouldShowChevron = hasDelayPassed && canScrollDown && !hasUserScrolled

  useEffect(() => {
    setEditedContent(post?.content ?? "")
    setEditedHashtags(post?.hashtags ?? [])
  }, [post?.content, post?.hashtags])

  useEffect(() => {
    const checkBodyScrollable = () => {
      updateBodyScrollState(contentSectionRef.current)
    }

    const rafId = requestAnimationFrame(checkBodyScrollable)
    window.addEventListener("resize", checkBodyScrollable)
    return () => {
      cancelAnimationFrame(rafId)
      window.removeEventListener("resize", checkBodyScrollable)
    }
  }, [post?.content, post?.hashtags])

  useEffect(() => {
    setHasDelayPassed(false)
    setHasUserScrolled(false)

    const timer = window.setTimeout(() => {
      setHasDelayPassed(true)
    }, 2000)

    return () => window.clearTimeout(timer)
  }, [post?.content, post?.hashtags])

  return (
    <main className="relative flex h-dvh flex-col bg-white">
      <section className="flex justify-center px-10 pb-3 pt-8 shrink-0">
        <StepProgress current={stepNum} />
      </section>

      <section
        ref={contentSectionRef}
        onScroll={handleBodyScroll}
        data-scrollable={isBodyScrollable}
        className="relative flex flex-1 flex-col overflow-y-auto pb-20"
      >
        <GeneratedPostCarousel photos={photos} />

        <GeneratedPostBody
          content={editedContent}
          hashtags={editedHashtags}
          onContentChange={setEditedContent}
          onHashtagsChange={setEditedHashtags}
        />

        <div className="flex items-center justify-center gap-3 px-5 pb-2 pt-5">
          <Button variant="white" size="sm" onClick={() => onExit?.({ content: editedContent, hashtags: editedHashtags })}>미리보기</Button>
          <Button variant="primary" size="sm" onClick={() => onPublish?.({ content: editedContent, hashtags: editedHashtags })}>발행하기</Button>
        </div>

        <div
          className={`pointer-events-none absolute inset-x-0 bottom-20 z-10 h-24 bg-gradient-to-t from-black/20 to-transparent transition-opacity duration-200 ${shouldShowChevron ? "opacity-100" : "opacity-0"}`}
          aria-hidden="true"
        />

        <div
          className={`pointer-events-none absolute bottom-20 left-1/2 z-20 -translate-x-1/2 transition-opacity duration-200 ${shouldShowChevron ? "opacity-100 animate-bounce" : "opacity-0"}`}
          aria-hidden="true"
        >
          <svg viewBox="0 0 50 30" className="h-7 w-10" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 4L25 25L46 4" stroke="#FF8A3D" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </section>

      <BottomTab />
    </main>
  )
}
