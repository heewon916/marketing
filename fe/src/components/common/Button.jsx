import InstagramGlyphGradient from '@/assets/Instagram_Glyph_Gradient.png';

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
  instagram: `
    bg-white border border-gray-300
    active:bg-gray-100
  `,
};

export default function Button({
  size = 'lg',
  variant = 'primary',
  children,
  className = '',
  ...props
}) {
  const isInstagram = variant === 'instagram';

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
      {isInstagram ? (
        <>
          <img
            src={InstagramGlyphGradient}
            alt=""
            className="mr-3 h-8 w-8 shrink-0"
            aria-hidden="true"
          />
          <span className="bg-gradient-to-r from-[#833AB4] via-[#E1306C] to-[#F77737] bg-clip-text text-transparent">
            Instagram
          </span>
          <span className="text-black">{children}</span>
        </>
      ) : null}
      {!isInstagram ? children : null}
    </button>
  );
}
