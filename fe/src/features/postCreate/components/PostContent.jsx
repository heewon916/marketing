import { useEffect, useRef } from "react"

function PostContent({ content = "", onChange, isEditMode = true }) {
  const textareaRef = useRef(null)

  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return

    const scrollContainer = textarea.closest("[data-scrollable]")
    const prevScrollTop = scrollContainer?.scrollTop ?? 0
    const prevHeight = textarea.offsetHeight

    textarea.style.height = "auto"
    textarea.style.height = `${textarea.scrollHeight}px`

    if (scrollContainer) {
      const nextHeight = textarea.offsetHeight
      scrollContainer.scrollTop = prevScrollTop + Math.max(0, nextHeight - prevHeight)
    }
  }, [content])

  if (!isEditMode) {
    return (
      <div className="rounded-2xl bg-gray-50 px-5 py-4 text-lg text-accent-100 leading-relaxed whitespace-pre-wrap">
        {content || "본문이 없습니다"}
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-gray-300 bg-white px-5 py-4 text-lg text-accent-100 leading-relaxed focus-within:border-accent-100 transition-colors">
      <textarea
        ref={textareaRef}
        rows={1}
        className="text-lg w-full resize-none overflow-hidden bg-transparent outline-none whitespace-pre-wrap min-h-[110px]"
        value={content}
        onChange={(e) => onChange?.(e.target.value)}
      />
    </div>
  )
}

export default PostContent