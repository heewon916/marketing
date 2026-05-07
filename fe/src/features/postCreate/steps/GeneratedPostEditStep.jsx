import { useEffect, useRef, useState } from "react"
import StepProgress from "@/components/common/StepProgress"
import Button from "@/components/common/Button"
import BottomTab from "@/components/common/BottomTab"
import GeneratedPostCarousel from "@/features/postCreate/components/GeneratedPostCarousel"
import GeneratedPostBody from "@/features/postCreate/components/GeneratedPostBody"
import ScrollFadeArrow from "@/components/common/ScrollFadeArrow"

export default function GeneratedPostEditStep({ post, photos = [], onPublish, onExit, stepNum }) {
  const [editedContent, setEditedContent] = useState(post?.content ?? "")
  const contentSectionRef = useRef(null)

  useEffect(() => {
    contentSectionRef.current?.scrollTo({ top: 0 })
  }, [])

  useEffect(() => {
    setEditedContent(post?.content ?? "")
  }, [post?.content])


  return (
    <main className="relative flex h-dvh flex-col bg-white">
      <section className="flex justify-center px-10 pb-3 pt-8 shrink-0">
        <StepProgress current={stepNum} />
      </section>

      <div className="absolute bottom-20 left-0 w-full z-20 pointer-events-none">
        <ScrollFadeArrow targetRef={contentSectionRef} />
      </div>

      <section
        ref={contentSectionRef}
        className="relative flex flex-1 flex-col overflow-y-auto pb-20"
      >
        <GeneratedPostCarousel photos={photos} />

        <GeneratedPostBody
          content={editedContent}
          onContentChange={setEditedContent}
        />

        <div className="flex items-center justify-center gap-3 px-5 pb-2 pt-5">
          <Button variant="white" size="sm" onClick={() => onExit?.({ content: editedContent })}>미리보기</Button>
          <Button variant="primary" size="sm" onClick={() => onPublish?.({ content: editedContent })}>발행하기</Button>
        </div>

      </section>

      <BottomTab />
    </main>
  )
}
