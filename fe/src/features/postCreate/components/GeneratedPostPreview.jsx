import { useState } from "react";
import {
  MoreVertical,
  Heart,
  MessageCircle,
  Repeat2,
  Send,
  Bookmark,
  UserRound,
} from "lucide-react";

function GeneratedPostPreview({ post, photos = [] }) {
  const [activeIndex, setActiveIndex] = useState(0);

  const handleScroll = (e) => {
    const el = e.currentTarget;
    const cardWidth = el.offsetWidth;
    const idx = Math.round(el.scrollLeft / cardWidth);
    setActiveIndex(Math.max(0, Math.min(idx, photos.length - 1)));
  };

  return (
    <div className="mt-2 rounded-lg border border-gray-200 bg-white">
      <header className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full border border-gray-300 bg-gray-100">
            <UserRound size={20} className="text-gray-400" />
          </div>
          <p className="text-[18px] font-semibold leading-none text-accent-100">
            insta_id
          </p>
        </div>

        <MoreVertical size={26} className="text-accent-100" />
      </header>

      <div
        onScroll={handleScroll}
        className="flex w-full snap-x snap-mandatory overflow-x-auto"
        style={{ scrollbarWidth: "none", WebkitOverflowScrolling: "touch" }}
      >
        {photos.length > 0 ? (
          photos.map((photo, i) => (
            <div
              key={photo.id ?? i}
              className="relative aspect-[384/514] w-full shrink-0 snap-center overflow-hidden bg-gray-200"
            >
              {photo.url ? (
                <img
                  src={photo.url}
                  alt={`generated-post-${i + 1}`}
                  className="h-full w-full object-cover"
                  draggable={false}
                />
              ) : (
                <div className="h-full w-full bg-gray-200" />
              )}
            </div>
          ))
        ) : (
          <div className="relative aspect-[384/514] w-full shrink-0 snap-center bg-gray-200" />
        )}
      </div>
      {photos.length > 1 && (
        <div className="flex justify-center gap-1.5 mt-3">
          {photos.map((_, i) => (
            <span
              key={i}
              className={`h-2 w-2 rounded-full ${
                i === activeIndex ? "bg-[#0095f6]" : "bg-gray-300"
              }`}
            />
          ))}
        </div>
      )}
      <div className="px-4 py-3">
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Heart size={30} className="fill-red-500 text-red-500" />
            <MessageCircle size={29} className="text-accent-100" />
            <Repeat2 size={29} className="text-accent-100" />
            <Send size={28} className="text-accent-100" />
          </div>

          <Bookmark size={29} className="text-accent-100" />
        </div>

        <p className="mt-2 whitespace-pre-wrap break-words text-[18px] leading-tight text-accent-100">
          <span className="font-semibold">insta_id </span>
          {post?.content ?? ""}
          {post?.hashtags?.length > 0 && (
            <span className="text-[#405987]">
              {post.hashtags.map((tag) => `#${tag}`).join(" ")}{" "}
            </span>
          )}
        </p>
      </div>
    </div>
  );
}

export default GeneratedPostPreview;
