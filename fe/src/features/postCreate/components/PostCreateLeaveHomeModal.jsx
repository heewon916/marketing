import Modal from '@/components/common/Modal';

export default function PostCreateLeaveHomeModal({
  isOpen,
  onClose,
  onConfirm,
  onCancel,
  children,
}) {
  const handleCancel = () => {
    onCancel?.();
    onClose?.();
  };

  const handleConfirm = () => {
    onConfirm?.();
    onClose?.();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={children ? undefined : `이동하시겠어요?`}
      description={children ? undefined : '페이지를 이동하면\n작성중인 내용이 사라져요.'}
      cancelText="아니오"
      confirmText="예"
      titleColor='primary'
      onCancel={handleCancel}
      onConfirm={handleConfirm}
    >
      {children}
    </Modal>
  );
}
