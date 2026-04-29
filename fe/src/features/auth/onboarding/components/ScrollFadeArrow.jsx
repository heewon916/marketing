import { useState, useEffect } from 'react';

export default function ScrollFadeArrow({ targetRef }) {
  const [isVisible, setIsVisible] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);

  useEffect(() => {
    const checkScrollable = () => {
      if (hasInteracted) return;

      const isScrollable = (targetRef && targetRef.current)
        ? targetRef.current.scrollHeight > targetRef.current.clientHeight
        : document.documentElement.scrollHeight > window.innerHeight;
      
      setIsVisible(isScrollable);
    };

    const timer = setTimeout(checkScrollable, 100);

    const handleInteraction = () => {
      if (!hasInteracted) {
        setHasInteracted(true);
        setIsVisible(false);
      }
    };

    // 타겟이 특정 박스면 그 박스에, 아니면 window에 이벤트 적용
    const target = (targetRef && targetRef.current) ? targetRef.current : window;

    target.addEventListener('scroll', handleInteraction, { passive: true });
    target.addEventListener('wheel', handleInteraction, { passive: true });
    target.addEventListener('touchmove', handleInteraction, { passive: true });
    window.addEventListener('resize', checkScrollable);

    return () => {
      clearTimeout(timer);
      target.removeEventListener('scroll', handleInteraction);
      target.removeEventListener('wheel', handleInteraction);
      target.removeEventListener('touchmove', handleInteraction);
      window.removeEventListener('resize', checkScrollable);
    };
  }, [hasInteracted, targetRef]);

  return (
    <div
      className={`
        /* 특정 박스 안일 때는 absolute, 전체 화면일 때는 fixed로 자동 변환! */
        ${targetRef ? 'absolute' : 'fixed'} 
        bottom-0 left-0 w-full h-40 
        bg-gradient-to-t from-white via-white/80 to-transparent 
        flex items-end justify-center pb-4 
        pointer-events-none transition-opacity duration-300
        ${isVisible ? 'opacity-100 z-10' : 'opacity-0 -z-10'}
      `}
    >
      <span 
        className="material-icons text-primary-100 animate-bounce"
        style={{ fontSize: '60px' }}
      >
        expand_more
      </span>
    </div>
  );
}