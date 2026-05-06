function PostContent({ content = "", onChange, isEditMode = true }) {
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
        className="text-lg w-full resize-none bg-transparent outline-none whitespace-pre-wrap min-h-[110px]"
        value={content}
        onChange={(e) => onChange?.(e.target.value)}
      />
    </div>
  )
}

export default PostContent