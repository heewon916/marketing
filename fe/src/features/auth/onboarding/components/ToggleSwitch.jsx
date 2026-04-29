export default function ToggleSwitch({ checked, onChange }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label="영업 여부 토글"
      onClick={onChange}
      className={`
        relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent 
        transition-colors duration-200 ease-in-out
        ${checked ? 'bg-primary-100' : 'bg-gray-800'}
      `}
    >
      <span
        className={`
          pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow
          transition duration-200 ease-in-out
          ${checked ? 'translate-x-4' : 'translate-x-0.5'}
        `}
      />
    </button>
  );
}