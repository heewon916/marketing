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
  const [isProfileImageError, setIsProfileImageError] = useState(false);

  const instagramUrl = instagramUsername
    ? `https://www.instagram.com/${instagramUsername.replace(/^@/, '')}`
    : null;

  const hasProfileImage = profileImageUrl && !isProfileImageError;

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

  const handleInstagramModalClose = () => {
    if (!isUpdating) {
      setIsInstagramModalOpen(false);
    }
  };

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

                  {/* 새로고침 버튼 영역 */}
                  <button
                    type="button"
                    onClick={() => setIsInstagramModalOpen(true)}
                    disabled={isUpdating}
                    className={[
                      'flex h-6 w-6 items-center justify-center rounded-full border border-gray-200 bg-gray-100 transition-all',
                      isUpdating
                        ? 'cursor-not-allowed opacity-50'
                        : 'text-gray-500 active:scale-90 active:border-primary-100 active:bg-surface-100 active:text-primary-100',
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

      <Modal
        isOpen={isInstagramModalOpen}
        onClose={handleInstagramModalClose}
        showClose={false}
        closeOnBackdrop={!isUpdating}
        title={`인스타그램 정보를\n업데이트할까요?`}
        description={`프로필 사진과 계정명을\n최신 정보로 불러옵니다.`}
        titleColor="primary"
        cancelText="취소"
        confirmText={isUpdating ? '업데이트 중' : '업데이트'}
        onCancel={handleInstagramModalClose}
        onConfirm={handleInstagramUpdate}
      />
    </>
  );
}
