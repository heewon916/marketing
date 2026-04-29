export default function CategoryChip({ label, isSelected, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        w-full h-[56px] text-xl font-bold rounded-2xl border transition-all duration-200
        ${
          isSelected
            ? 'border-primary-100 bg-surface-200 text-primary-100'
            : 'border-gray-200 bg-gray-50 text-gray-600'
        }
      `}
    >
      {label}
    </button>
  );
}