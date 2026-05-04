function GeneratedPostCarousel({ photos = [], onScroll }) {
  return (
    <section className="shrink-0 w-full">
      <div
        onScroll={onScroll}
        className="flex w-full snap-x snap-mandatory overflow-x-auto"
        style={{ scrollbarWidth: "none", WebkitOverflowScrolling: "touch" }}
      >
        {photos.length > 0 ? (
          photos.map((photo, i) => (
            <div
              key={photo.id ?? i}
              className="relative shrink-0 snap-center w-full aspect-[384/514] overflow-hidden"
            >
              {photo.url ? (
                <img
                  src={photo.url}
                  alt={`photo-${i + 1}`}
                  className="h-full w-full object-cover"
                  draggable={false}
                />
              ) : (
                <div className="h-full w-full bg-primary-100" />
              )}
              {photos.length > 1 && (
                <div className="absolute top-4 right-4 rounded-full bg-accent-100/80 px-3 py-1 text-sm font-semibold text-white">
                  {i + 1} / {photos.length}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="relative shrink-0 snap-center w-full aspect-[384/514] bg-primary-100">
            <div className="absolute top-4 right-4 rounded-full bg-accent-100/80 px-3 py-1 text-sm font-semibold text-white">
              1 / 1
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

export default GeneratedPostCarousel
