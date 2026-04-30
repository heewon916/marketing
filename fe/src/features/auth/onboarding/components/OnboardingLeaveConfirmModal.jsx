import Modal from '@/components/common/Modal.jsx';
import Button from '@/components/common/Button.jsx';

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
    >
      <div className="mt-2 flex flex-col items-center text-center">
        <p className="text-2xl leading-snug text-accent-100">
          지금 나가면
          <br />
          진행 중인 설정이 사라져요.
        </p>

        <p className="mt-3 text-2xl font-extrabold text-primary-100">
          나가시겠어요?
        </p>

        <div className="mt-8 flex w-full gap-3">
          <Button
            variant="white"
            className="!h-[56px] !flex-1 rounded-2xl text-[18px] font-bold"
            onClick={onCancel}
          >
            아니요
          </Button>

          <Button
            variant="primary"
            className="!h-[56px] !flex-1 rounded-2xl text-[18px] font-bold"
            onClick={onConfirm}
          >
            나가기
          </Button>
        </div>
      </div>
    </Modal>
  );
}
