const sizeStyles = {
  sm: 'w-[150px] h-[56px] text-xl rounded-xl',
  lg: 'w-[330px] h-[56px] text-xl rounded-xl',
};

const variantStyles = {
  primary: `
    bg-primary-100 text-white
    active:brightness-95
  `,
  white: `
    bg-white text-primary-600 border border-gray-300
    active:bg-gray-100
  `,
  navy: `
    bg-accent-100 text-white
    active:brightness-90
  `,
    danger: `
    bg-red-500 text-white border border-red-500
    active:brightness-95
  `,
};

export default function Button({
  size = 'lg',
  variant = 'primary',
  children,
  className = '',
  ...props
}) {
  return (
    <button
      className={`
        flex items-center justify-center
        font-medium
        transition-colors
        disabled:opacity-50 disabled:cursor-not-allowed
        ${sizeStyles[size]}
        ${variantStyles[variant]}
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
}
