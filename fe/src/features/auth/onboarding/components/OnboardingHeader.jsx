export default function OnboardingHeader({ title, emphasis, subtitle }) {
  return (
    <div className="text-left">
      <h1 className="text-3xl font-bold leading-snug text-gray-900">
        {title}
      </h1>

      {emphasis && (
        <p className="mt-5 text-lg font-bold text-gray-900">
          {emphasis}
        </p>
      )}

      {subtitle && (
        <p className={`${emphasis ? 'mt-1' : 'mt-3'} text-lg leading-relaxed text-gray-500`}>
          {subtitle}
        </p>
      )}
    </div>
  );
}