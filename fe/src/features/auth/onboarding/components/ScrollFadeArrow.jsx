export default function ScrollFadeArrow({ isVisible }) {
  return (
    <div
      className={`
        absolute bottom-0 left-0 w-full h-24 
        bg-gradient-to-t from-white via-white/80 to-transparent 
        flex items-end justify-center pb-2 
        pointer-events-none transition-opacity duration-300
        ${isVisible ? 'opacity-100' : 'opacity-0'}
      `}
    >
      <span className="material-icons text-5xl text-primary-100 animate-bounce">
        expand_more
      </span>
    </div>
  );
}