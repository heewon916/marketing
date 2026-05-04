export default function ProfileCard({
  storeName,
  instagramUsername,
  onClick,
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex w-full items-center justify-between gap-4 rounded-[28px] bg-white p-5 text-left shadow-sm ring-1 ring-surface-100 transition-all duration-300 hover:shadow-md active:scale-[0.98]"
    >
      <div className="flex flex-1 items-center gap-4 min-w-0">
        {/* 프로필 이미지 플레이스홀더 (테마 컬러 적용) */}
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-surface-100 text-primary-100">
          <span className="material-icons text-[32px]">storefront</span>
        </div>

        <div className="flex flex-col min-w-0">
          <strong className="truncate text-[22px] font-extrabold tracking-tight text-accent-100">
            {storeName}
          </strong>
          <span className="mt-0.5 truncate text-[15px] font-medium text-gray-500">
            {instagramUsername}
          </span>
        </div>
      </div>

      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-200 text-gray-400 transition-colors group-hover:bg-surface-100 group-hover:text-primary-100">
        <span className="material-icons text-[24px]">chevron_right</span>
      </div>
    </button>
  );
}
