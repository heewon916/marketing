export default function RoundedInput({ icon, className = '', ...props }) {
  return (
    <div className="relative w-full">
      <input
        type="text"
        className={`
          w-full px-4 py-3 border border-gray-200 rounded-xl text-[17px] font-medium text-gray-900 
          outline-none transition-all placeholder:text-gray-400
          focus:border-primary-100 focus:ring-4 focus:ring-primary-100/10 
          disabled:bg-gray-100 disabled:text-gray-400 disabled:border-transparent
          ${icon ? 'pr-12' : ''} ${className}
        `}
        {...props}
      />

      {icon && (
        <span className="material-icons absolute right-4 top-1/2 -translate-y-1/2 text-gray-600 pointer-events-none">
          {icon}
        </span>
      )}
    </div>
  );
}