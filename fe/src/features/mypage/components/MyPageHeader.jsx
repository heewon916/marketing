import { useState } from 'react';
import { IoPerson } from 'react-icons/io5';
import Modal from '@/components/common/Modal';
import Button from '@/components/common/Button';
import { registerFcmToken } from '@/features/notification/api/FcmApi';

export default function MyPageHeader({
  title,
  storeName,
  instagramUsername,
  profileImageUrl,
  onInstagramUpdate,
  showBackButton = false,
  onBack,
}) {
  const [isUpdating, setIsUpdating] = useState(false);
  const [isInstagramModalOpen, setIsInstagramModalOpen] = useState(false);

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

      setIsInstagramModalOpen(false);
    } finally {
      setIsUpdating(false);
    }
  };

  const [isProfileImageError, setIsProfileImageError] = useState(false);

  const hasProfileImage = profileImageUrl && !isProfileImageError;

  return (
    <>
      <header className="relative w-full bg-white">
        {showBackButton && (
          <button
            type="button"
            onClick={onBack}
            className="absolute left-5 top-5 z-10 flex h-8 w-8 items-center justify-center text-accent-100 transition-colors active:text-primary-100"
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
              <strong className="text-[28px] font-semibold tracking-tight text-black">
                {storeName}
              </strong>

              {instagramUsername && (
                <div className="mt-1 flex items-center gap-2">
                  <a
                    href={instagramUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex w-fit items-center text-[16px] text-primary-100 transition-colors active:opacity-70"
                  >
                    <span className="border-b border-primary-100">
                      {instagramUsername}
                    </span>
                  </a>

                  {/* 새로고침(업데이트) 버튼 */}
                  <button
                    type="button"
                    onClick={() => setIsInstagramModalOpen(true)}
                    disabled={isUpdating}
                    className={[
                      'flex h-6 w-6 items-center justify-center rounded-full bg-gray-100 border border-gray-200 transition-all',
                      isUpdating
                        ? 'cursor-not-allowed opacity-50'
                        : 'text-gray-500 active:scale-90 active:bg-surface-100 active:text-primary-100 active:border-primary-100',
                    ].join(' ')}
                    aria-label="인스타그램 정보 업데이트"
                  >
                  <span
                    className={`material-icons ${isUpdating ? 'animate-spin' : ''}`}
                    style={{ fontSize: '16px' }}
                  >
                    sync
                  </span>
                  </button>
                  {/* 끝: 새로고침(업데이트) 버튼 */}
                </div>
              )}
            </div>

            <div
              className="h-[80px] w-[80px] shrink-0 overflow-hidden rounded-full bg-gray-300"
              onClick={() => registerFcmToken({ requestPermission: true })}
            >
              {hasProfileImage ? (
                <img
                  src={profileImageUrl}
                  alt="프로필"
                  className="h-full w-full object-cover"
                  onError={() => setIsProfileImageError(true)}
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center">
                  <IoPerson className="translate-y-3 text-[70px] text-gray-100" />
                </div>
              )}
            </div>
          </div>
        )}
      </header>

      {isInstagramModalOpen && (
        <Modal
          isOpen={isInstagramModalOpen}
          onClose={() => {
            if (!isUpdating) {
              setIsInstagramModalOpen(false);
            }
          }}
          showClose={false}
          closeOnBackdrop={!isUpdating}
        >
          <div className="text-center">
            <h2 className="text-[20px] font-bold text-accent-100">
              인스타그램 정보를 업데이트할까요?
            </h2>

            <p className="mt-3 text-[18px] leading-relaxed text-gray-500">
              프로필 사진과 계정명을
              <br />
              최신 정보로 불러옵니다.
            </p>

            <div className="mt-7 flex justify-center gap-3">
              <Button
                size="sm"
                variant="white"
                onClick={() => {
                  if (!isUpdating) {
                    setIsInstagramModalOpen(false);
                  }
                }}
                disabled={isUpdating}
                className="text-[18px] font-bold"
              >
                취소
              </Button>

              <Button
                size="sm"
                variant="primary"
                onClick={handleInstagramUpdate}
                disabled={isUpdating}
                className="text-[18px] font-bold"
              >
                {isUpdating ? '업데이트 중' : '업데이트'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
