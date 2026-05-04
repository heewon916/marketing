import { HiOutlineTrash } from "react-icons/hi"

function PhotoDeleteButton({ onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex h-14 w-14 items-center justify-center rounded-full border border-gray-300 bg-white text-accent-100 active:bg-gray-100"
      aria-label="사진 삭제"
    >
      <HiOutlineTrash className="text-[28px]" />
    </button>
  )
}

export default PhotoDeleteButton
