import { useState } from 'react';
import CharacterLove from '@/assets/character/CharacterLove.png';

export default function MyPageHeader({
  title,
  storeName,
  instagramUsername,
  onLogout,
  onInstagramUpdate,
  showBackButton = false,
  onBack,
}) {
  const [isUpdating, setIsUpdating] = useState(false);

  const instagramUrl = instagramUsername
    ? `https://www.instagram.com/${instagramUsername.replace(/^@/, '')}`
    : null;

  const handleInstagramUpdate = async () => {
    if (isUpdating) return;

    try {
      setIsUpdating(true);

      if (onInstagramUpdate) {
        await onInstagramUpdate();
      } else {
        await new Promise((resolve) => setTimeout(resolve, 1500));
      }
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <header className="relative w-full bg-white">
      {showBackButton && (
        <button
          type="button"
          onClick={onBack}
          className="absolute left-5 top-5 z-10 flex h-8 w-8 items-center justify-center text-accent-100 transition-colors hover:text-primary-100"
          aria-label="뒤로가기"
        >
          <span className="material-icons text-[28px]">chevron_left</span>
        </button>
      )}

      {title && !storeName && (
        <div className="mx-auto flex w-full max-w-[430px] items-center justify-center px-5 pb-4 pt-2">
          <h1 className="text-[20px] font-bold text-accent-100">{title}</h1>
        </div>
      )}

      {storeName && (
        <div className="mx-auto flex w-full max-w-[430px] items-start justify-between px-9 pb-4 pt-10">
          <div className="flex flex-col">
            <strong className="text-[26px] font-extrabold tracking-tight text-black">
              {storeName}
            </strong>

            {instagramUsername && (
              <a
                href={instagramUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex w-fit items-center text-[15px] text-primary-100 transition-colors hover:text-primary-100"
              >
                <span className="border-b border-primary-100">
                  {instagramUsername}
                </span>
              </a>
            )}

            <div className="mt-3 flex items-center gap-2">
              <button
                type="button"
                onClick={handleInstagramUpdate}
                disabled={isUpdating}
                className={[
                  'w-[138px] rounded-lg border border-gray-200 py-1 text-[13px] font-medium transition-all',
                  isUpdating
                    ? 'cursor-not-allowed text-gray-300'
                    : 'text-gray-400 hover:border-primary-100',
                ].join(' ')}
              >
                {isUpdating ? '업데이트 중...' : '인스타그램 업데이트'}
              </button>

              {onLogout && (
                <button
                  type="button"
                  onClick={onLogout}
                  className="h-8 rounded-lg border border-gray-200 px-3 text-[13px] font-medium text-gray-400 transition-colors hover:border-primary-100 hover:text-primary-100 active:scale-95"
                >
                  로그아웃
                </button>
              )}
            </div>
          </div>

          <div className="h-[80px] w-[80px] shrink-0 overflow-hidden rounded-full bg-surface-100 border border-gray-300">
            <img
              src={CharacterLove}
              alt="프로필 캐릭터"
              className="h-full w-full object-cover"
            />
          </div>
        </div>
      )}
    </header>
  );
}
