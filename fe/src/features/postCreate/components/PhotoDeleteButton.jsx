import { HiOutlineTrash } from "react-icons/hi"

function PhotoDeleteButton({ onClick, disabled = false }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex h-14 w-14 items-center justify-center rounded-full border transition-colors ${
        disabled
          ? "cursor-not-allowed border-gray-200 bg-gray-100 text-accent-100/40"
          : "border-gray-300 bg-white text-accent-100 active:bg-gray-100"
      }`}
      aria-label="사진 삭제"
    >
      <HiOutlineTrash className="text-[28px]" />
    </button>
  )
}

export default PhotoDeleteButton
