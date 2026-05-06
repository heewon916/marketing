import CardShell from './CardShell';

export default function ProfileCard({
  storeName,
  instagramUsername,
  onClick,
}) {
  return (
    <CardShell
      as="button"
      onClick={onClick}
      className="group flex items-center justify-between gap-4 p-5 text-left"
      aria-label="계정 정보로 이동"
    >
      <div className="flex min-w-0 flex-1 items-center gap-4">
        <div className="flex min-w-0 flex-col">
          <strong className="truncate text-[22px] font-extrabold tracking-tight text-accent-100">
            {storeName}
          </strong>
          <span className="mt-0.5 truncate text-[15px] font-medium text-gray-500">
            {instagramUsername}
          </span>
        </div>
      </div>

      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-gray-400">
        <span className="material-icons text-[24px]">chevron_right</span>
      </div>
    </CardShell>
  );
}
