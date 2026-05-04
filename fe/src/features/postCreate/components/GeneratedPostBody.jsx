import PostContent from "@/features/postCreate/components/PostContent"
import PostHashtags from "@/features/postCreate/components/PostHashtags"

function GeneratedPostBody({ content = "", hashtags = [], onContentChange, onHashtagsChange }) {
  return (
    <section className="px-5 pt-5 flex flex-col gap-3">
      <div>
        <h2 className="text-xl font-bold text-accent-100 mb-3">본문</h2>
        <PostContent content={content} onChange={onContentChange} />
      </div>
      <div>
        <h2 className="text-xl font-bold text-accent-100 mb-3 mt-3">해시태그</h2>
        <PostHashtags hashtags={hashtags} onChange={onHashtagsChange} />
      </div>
    </section>
  )
}

export default GeneratedPostBody
