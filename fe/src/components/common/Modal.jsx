import Button from '@/components/common/Button';

const TITLE_COLOR_CLASS = {
  accent: 'text-accent-100',
  primary: 'text-primary-100',
};

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
  titleColor = 'accent',

  confirmVariant,
  confirmDisabled = false,
  cancelDisabled = false,
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
    if (cancelDisabled) return;

    if (onCancel) {
      onCancel();
      return;
    }

    onClose?.();
  };

  // 확인 버튼 처리
  const handleConfirm = () => {
    if (confirmDisabled) return;

    if (onConfirm) {
      onConfirm();
      return;
    }

    onClose?.();
  };

  // 제목 색상 처리
  const titleColorClass =
    variant === 'danger'
      ? 'text-red-500'
      : TITLE_COLOR_CLASS[titleColor] || TITLE_COLOR_CLASS.accent;

  // 확인 버튼 색상 처리
  const confirmButtonVariant =
    confirmVariant || (variant === 'danger' ? 'danger' : 'primary');

  return (
    <div
      className="fixed inset-0 z-[999] flex items-center justify-center bg-black/20"
      onClick={handleBackdropClick}
    >
      {/* 모달 컨테이너 */}
      <div
        className="relative w-[90%] max-w-[360px] rounded-3xl bg-white px-6 pb-8 pt-12"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 닫기 버튼 영역 */}
        {showClose && (
          <button
            type="button"
            onClick={onClose}
            className="absolute right-5 top-5 text-gray-700"
          >
            <span className="material-icons text-2xl">close</span>
          </button>
        )}

        {/* 기본 텍스트 영역 */}
        {(title || description) && (
          <div className="text-center">
            {title && (
              <h2
                className={`whitespace-pre-line text-[24px] font-bold leading-snug ${titleColorClass}`}
              >
                {title}
              </h2>
            )}

            {description && (
              <p className="mt-4 whitespace-pre-line text-[18px] font-medium leading-relaxed text-accent-100">
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
                disabled={cancelDisabled}
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
                variant={confirmButtonVariant}
                disabled={confirmDisabled}
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
