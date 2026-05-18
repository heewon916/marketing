import Modal from '@/components/common/Modal.jsx';

export default function OnboardingLeaveConfirmModal({
  isOpen,
  onCancel,
  onConfirm,
}) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onCancel}
      showClose={false}
      closeOnBackdrop={false}
      title={`지금 나가면\n진행 중인 설정이 사라져요.`}
      description="나가시겠어요?"
      descriptionClassName="!mt-3 text-primary-100 !text-[24px] !font-extrabold !leading-snug"
      cancelText="아니요"
      confirmText="나가기"
      onCancel={onCancel}
      onConfirm={onConfirm}
    />
  );
}
