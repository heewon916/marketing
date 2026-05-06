export default function CardShell({
  as: Component = 'section',
  children,
  className = '',
  type,
  onClick,
  ...props
}) {
  const isButton = Component === 'button';

  return (
    <Component
      type={isButton ? type || 'button' : undefined}
      onClick={onClick}
      className={[
        'w-full rounded-[20px] border border-gray-200 bg-white',
        className,
      ].join(' ')}
      {...props}
    >
      {children}
    </Component>
  );
}
