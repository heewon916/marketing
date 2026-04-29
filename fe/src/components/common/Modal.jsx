export default function Modal({
  isOpen,
  onClose,
  children,
  showClose = true,
}) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[999] flex items-center justify-center bg-black/20"
      onClick={onClose}
    >
      
      {/* 모달 박스 */}
      <div
        className="relative w-[90%] max-w-[360px] bg-white rounded-3xl px-6 pt-12 pb-8"
        onClick={(e) => e.stopPropagation()}
      >

        {/* 닫기 버튼 */}
        {showClose && (
          <button
            onClick={onClose}
            className="absolute top-5 right-5 text-gray-700"
          >
            <span className="material-icons text-2xl">close</span>
          </button>
        )}

        {/* 컨텐츠 */}
        {children}
      </div>
    </div>
  );
}