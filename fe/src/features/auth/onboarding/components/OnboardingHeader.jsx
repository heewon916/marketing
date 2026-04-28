export default function OnboardingHeader({ title, subtitle }) {
  return (
    <div className="text-left">
      <h1 className="text-3xl font-bold leading-snug text-gray-900">
        {title}
      </h1>
      {subtitle && (
        <p className="mt-3 text-md leading-relaxed text-gray-500">
          {subtitle}
        </p>
      )}
    </div>
  );
}