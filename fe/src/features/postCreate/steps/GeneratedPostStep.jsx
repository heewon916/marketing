import { useRef } from "react"
import StepProgress from "@/components/common/StepProgress"
import Button from "@/components/common/Button"
import BottomTab from "@/components/common/BottomTab"
import GeneratedPostPreview from "@/features/postCreate/components/GeneratedPostPreview"
import ScrollFadeArrow from "@/components/common/ScrollFadeArrow"

export default function GeneratedPostStep({ post, photos = [], onEdit, onPublish, stepNum }) {
  const scrollRef = useRef(null)

  return (
    <main className="relative flex h-dvh flex-col bg-white">
      <section className="flex justify-center px-10 pb-3 pt-8 shrink-0">
        <StepProgress current={stepNum} />
      </section>

      <div className="absolute bottom-20 left-0 w-full z-20 pointer-events-none">
        <ScrollFadeArrow targetRef={scrollRef} />
      </div>

      <section ref={scrollRef} className="relative flex flex-1 flex-col overflow-y-auto px-6 pb-20">
        <GeneratedPostPreview post={post} photos={photos} />

        <div className="mt-auto pb-3 pt-5">
          <div className="flex items-center justify-center gap-3 px-3">
            <Button variant="white" size="sm" onClick={onEdit}>수정하기</Button>
            <Button variant="primary" size="sm" onClick={() => onPublish?.(post)}>발행하기</Button>
          </div>
        </div>
      </section>

      <BottomTab />
    </main>
  )
}
