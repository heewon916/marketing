function PostContent({ content = "", onChange }) {
  return (
    <div className="rounded-2xl bg-gray-50 px-5 py-4 text-lg text-accent-100 leading-relaxed">
      <textarea
        className="text-lg w-full resize-none bg-transparent outline-none whitespace-pre-wrap min-h-[120px]"
        value={content}
        onChange={(e) => onChange?.(e.target.value)}
      />
    </div>
  )
}

export default PostContent
