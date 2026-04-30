import Modal from '@/components/common/Modal.jsx';
import Button from '@/components/common/Button.jsx';

export default function StoreNotFoundModal({
  isOpen,
  onManualInput,
  onGoHome,
}) {
  return (
    <Modal
      isOpen={isOpen}
      showClose={false}
      closeOnBackdrop={false}
    >
      <div className="mt-2 flex flex-col items-center text-center">
        <div className="mb-3 whitespace-nowrap text-[22px] font-bold text-primary-100">
          가게 정보를 찾을 수 없어요.
        </div>

        <div className="mb-8 text-[19px] font-semibold leading-snug text-accent-100">
          네이버 플레이스에 등록되어
          <br />
          있는지 확인해 주세요.
        </div>

        <div className="flex w-full flex-col gap-3">
          <Button
            variant="primary"
            className="!h-[56px] !w-full rounded-2xl text-[18px] font-bold"
            onClick={onManualInput}
          >
            직접 가게 정보 입력하기
          </Button>

          <Button
            variant="white"
            className="!h-[56px] !w-full rounded-2xl text-[18px] font-bold"
            onClick={onGoHome}
          >
            메인으로 돌아가기
          </Button>
        </div>
      </div>
    </Modal>
  );
}
