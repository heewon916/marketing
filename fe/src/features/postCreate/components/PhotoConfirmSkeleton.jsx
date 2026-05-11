import StepProgress from "@/components/common/StepProgress"
import BottomTab from "@/components/common/BottomTab"

const PEEK = 30
const GAP = 16

function PhotoConfirmSkeleton() {
  return (
    <main className="relative flex h-dvh flex-col bg-white">
      <section className="flex justify-center px-10 pt-8 pb-3 shrink-0">
        <StepProgress current={3} />
      </section>

      <section className="flex flex-1 items-center justify-center overflow-hidden gap-5 pb-40 px-5">
        <div
          className="flex w-full snap-x snap-mandatory overflow-x-hidden"
          style={{
            gap: GAP,
            scrollbarWidth: "none",
            WebkitOverflowScrolling: "touch",
          }}
        >
          {[0, 1, 2].map((index) => (
            <div
              key={index}
              className="relative shrink-0 snap-center overflow-hidden rounded-[28px] aspect-[384/514] bg-gray-100"
              style={{
                width: `calc(100% - ${PEEK * 2}px)`,
                marginLeft: index === 0 ? PEEK : 0,
                marginRight: index === 2 ? PEEK : 0,
              }}
            >
              <div className="h-full w-full animate-pulse bg-gradient-to-br from-gray-100 via-gray-200 to-gray-100" />
              <div className="absolute left-4 top-4 h-7 w-20 rounded-full bg-white/70 animate-pulse" />
              <div className="absolute inset-x-4 bottom-4 space-y-2">
                <div className="h-4 w-3/4 rounded-full bg-white/70 animate-pulse" />
                <div className="h-4 w-1/2 rounded-full bg-white/60 animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="fixed bottom-20 left-1/2 z-20 w-full max-w-md -translate-x-1/2 px-4 pb-4">
        <div className="flex items-center justify-center gap-3">
          <div className="h-11 w-24 rounded-full bg-gray-200 animate-pulse" />
          <div className="h-11 w-24 rounded-full bg-gray-300 animate-pulse" />
        </div>
      </div>

      <BottomTab />
    </main>
  )
}

export default PhotoConfirmSkeleton
