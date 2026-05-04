function PhotoConfirmCarousel({ photos, trackRef, onScroll, peek = 30, gap = 16 }) {
  return (
    <div
      ref={trackRef}
      onScroll={onScroll}
      className="flex w-full snap-x snap-mandatory overflow-x-auto"
      style={{
        gap,
        scrollbarWidth: "none",
        WebkitOverflowScrolling: "touch",
      }}
    >
      {photos.map((photo, i) => (
        <div
          key={photo.id ?? i}
          className="relative shrink-0 snap-center overflow-hidden rounded-[28px] aspect-[384/514]"
          style={{
            width: `calc(100% - ${peek * 2}px)`,
            marginLeft: i === 0 ? peek : 0,
            marginRight: i === photos.length - 1 ? peek : 0,
          }}
        >
          <div className="h-full w-full bg-gray-100">
            {photo.url && (
              <img
                src={photo.url}
                alt={`photo-${i + 1}`}
                className="h-full w-full object-cover"
                draggable={false}
              />
            )}
          </div>

          <div className="absolute top-4 right-4 rounded-full bg-accent-100/80 px-3 py-1 text-sm font-semibold text-white">
            {i + 1} / {photos.length}
          </div>
        </div>
      ))}
    </div>
  )
}

export default PhotoConfirmCarousel
