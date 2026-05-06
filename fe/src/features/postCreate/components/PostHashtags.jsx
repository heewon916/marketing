import { useState } from "react"

function PostHashtags({ hashtags = [], onChange, isEditMode = true }) {
  const [inputValue, setInputValue] = useState("")
  const [isAdding, setIsAdding] = useState(false)

  const normalizeTag = (raw) => raw.replace(/^#+/, "").trim()

  const addTag = (rawValue) => {
    const nextTag = normalizeTag(rawValue)
    if (!nextTag) return false
    if (hashtags.includes(nextTag)) return false
    onChange?.([...hashtags, nextTag])
    return true
  }

  const handleKeyDown = (e) => {
    const isCommitKey = e.key === "Enter"

    if (isCommitKey) {
      e.preventDefault()
      const isAdded = addTag(inputValue)
      if (isAdded) {
        setInputValue("")
        setIsAdding(false)
      }
      return
    }

    if (e.key === "Escape") {
      setIsAdding(false)
      setInputValue("")
      return
    }

    if (e.key === "Backspace" && !inputValue && !isAdding && hashtags.length > 0) {
      onChange?.(hashtags.slice(0, -1))
    }
  }

  const handleRemove = (index) => {
    onChange?.(hashtags.filter((_, i) => i !== index))
  }

  const handleAddClick = () => {
    if (!isAdding) {
      setIsAdding(true)
      return
    }

    const isAdded = addTag(inputValue)
    if (isAdded) {
      setInputValue("")
      setIsAdding(false)
    }
  }

  if (!isEditMode) {
    return (
      <div className="rounded-2xl bg-gray-50 px-4 py-3 text-accent-100">
        <div className="flex min-h-12 flex-wrap items-center gap-2">
          {hashtags.length === 0 ? (
            <span className="text-accent-100/50">해시태그가 없습니다</span>
          ) : (
            hashtags.map((tag, index) => (
              <span
                key={`${tag}-${index}`}
                className="inline-flex items-center gap-1 rounded-full bg-accent-50 px-3 py-1 text-lg font-medium text-accent-100"
              >
                #{tag}
              </span>
            ))
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-2xl bg-gray-50 px-4 py-3 text-accent-100">
      <div className="flex min-h-12 flex-wrap items-center gap-2">
        {hashtags.map((tag, index) => (
          <span
            key={`${tag}-${index}`}
            className="inline-flex items-center gap-1 rounded-full bg-accent-50 px-3 py-1 text-lg font-medium text-accent-100"
          >
            #{tag}
            <button
              type="button"
              aria-label={`remove-${tag}`}
              className="text-accent-100/70 hover:text-accent-100 "
              onClick={() => handleRemove(index)}
            >
              x
            </button>
          </span>
        ))}

        {isAdding ? (
          <div className="inline-flex items-center gap-2 rounded-full border border-accent-100/30 bg-white px-3 py-1">
            <span className="text-accent-100">#</span>
            <input
              autoFocus
              className="w-24 bg-transparent text-sm outline-none"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="해시태그"
            />
            <button
              type="button"
              onClick={handleAddClick}
              className="text-sm font-semibold text-accent-100"
            >
              추가
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={handleAddClick}
            className="inline-flex items-center rounded-full border border-dashed border-accent-100/50 px-3 py-1 text-sm font-medium text-accent-100"
          >
            + 새 해시태그 추가
          </button>
        )}
      </div>
    </div>
  )
}

export default PostHashtags
