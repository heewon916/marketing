import PostContent from "@/features/postCreate/components/PostContent"

function GeneratedPostBody({ content = "", onContentChange }) {
  return (
    <section className="px-5 pt-5 flex flex-col gap-3">
      <div>
        <h2 className="text-xl font-bold text-accent-100 mb-3">본문</h2>
        <PostContent content={content} onChange={onContentChange} isEditMode />
      </div>
    </section>
  )
}

export default GeneratedPostBody
