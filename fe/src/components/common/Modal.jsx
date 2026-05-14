import Button from '@/components/common/Button';

export default function Modal({
  isOpen,
  onClose,
  children,
  showClose = true,
  closeOnBackdrop = true,

  title,
  description,
  confirmText,
  cancelText,
  onConfirm,
  onCancel,
  variant = 'default',
}) {
  if (!isOpen) return null;

  // 배경 클릭 처리
  const handleBackdropClick = () => {
    if (closeOnBackdrop) {
      onClose?.();
    }
  };

  // 취소 버튼 처리
  const handleCancel = () => {
    if (onCancel) {
      onCancel();
      return;
    }

    onClose?.();
  };

  // 확인 버튼 처리
  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm();
      return;
    }

    onClose?.();
  };

  // 모달 타입별 스타일
  const titleColorClass =
    variant === 'danger' ? 'text-red-500' : 'text-accent-100';

  return (
    <div
      className="fixed inset-0 z-[999] flex items-center justify-center bg-black/20"
      onClick={handleBackdropClick}
    >
      {/* 모달 컨테이너 */}
      <div
        className="relative w-[90%] max-w-[360px] bg-white rounded-3xl px-6 pt-12 pb-8"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 닫기 버튼 영역 */}
        {showClose && (
          <button
            type="button"
            onClick={onClose}
            className="absolute top-5 right-5 text-gray-700"
          >
            <span className="material-icons text-2xl">close</span>
          </button>
        )}

        {/* 기본 텍스트 영역 */}
        {(title || description) && (
          <div className="text-center">
            {title && (
              <h2
                className={`text-[22px] font-bold leading-snug ${titleColorClass}`}
              >
                {title}
              </h2>
            )}

            {description && (
              <p className="mt-4 whitespace-pre-line text-[17px] font-medium leading-relaxed text-gray-500">
                {description}
              </p>
            )}
          </div>
        )}

        {/* 커스텀 콘텐츠 영역 */}
        {children}

        {/* 하단 버튼 영역 */}
        {(confirmText || cancelText) && (
          <div className="mt-8 flex gap-3">
            {cancelText && (
              <Button
                type="button"
                size="sm"
                variant="white"
                className="flex-1 text-[18px] font-bold"
                onClick={handleCancel}
              >
                {cancelText}
              </Button>
            )}

            {confirmText && (
              <Button
                type="button"
                size="sm"
                variant={variant === 'danger' ? 'danger' : 'primary'}
                className="flex-1 text-[18px] font-bold"
                onClick={handleConfirm}
              >
                {confirmText}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
