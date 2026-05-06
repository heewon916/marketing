import PostContent from "@/features/postCreate/components/PostContent"
import PostHashtags from "@/features/postCreate/components/PostHashtags"

function GeneratedPostBody({ content = "", hashtags = [], onContentChange, onHashtagsChange, isEditMode = true, onEditModeToggle }) {
  return (
    <section className="px-5 pt-5 flex flex-col gap-3">
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-bold text-accent-100">본문</h2>
          <button
            type="button"
            onClick={onEditModeToggle}
            className="text-sm font-medium text-accent-100 hover:text-accent-50 transition-colors"
            aria-label="toggle edit mode"
          >
            {isEditMode ? "완료" : "수정"}
          </button>
        </div>
        <PostContent content={content} onChange={onContentChange} isEditMode={isEditMode} />
      </div>
      <div>
        <h2 className="text-xl font-bold text-accent-100 mb-3 mt-3">해시태그</h2>
        <PostHashtags hashtags={hashtags} onChange={onHashtagsChange} isEditMode={isEditMode} />
      </div>
    </section>
  )
}

export default GeneratedPostBody
