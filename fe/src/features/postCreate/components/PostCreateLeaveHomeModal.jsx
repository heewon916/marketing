import Button from "@/components/common/Button"
import Modal from "@/components/common/Modal"

export default function PostCreateLeaveHomeModal({
  isOpen,
  onClose,
  onConfirm,
  onCancel,
  children,
}) {
  const handleCancel = () => {
    onCancel?.()
    onClose?.()
  }

  const handleConfirm = () => {
    onConfirm?.()
    onClose?.()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="flex flex-col items-center gap-6">
        {children ?? (
          <p className="text-center text-gray-700 text-2xl font-medium">
            페이지를 이동하면
            <br /> 작성중인 내용이 사라져요.
            <br /> <span className="font-bold text-primary-100">이동하시겠어요?</span>
          </p>
        )}
        <div className="flex w-full items-center justify-center gap-3">
          <Button type="button" size="sm" variant="white" onClick={handleCancel}>
            아니오
          </Button>
          <Button type="button" size="sm" variant="primary" onClick={handleConfirm}>
            예
          </Button>
        </div>
      </div>
    </Modal>
  )
}
