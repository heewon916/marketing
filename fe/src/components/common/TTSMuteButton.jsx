import { useState } from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { getTTSMuted, toggleTTSMuted } from '@/utils/tts';

export default function TTSMuteButton({ className = '' }) {
  const [isMuted, setIsMuted] = useState(getTTSMuted());

  const handleToggle = () => {
    const nextMuted = toggleTTSMuted();
    setIsMuted(nextMuted);
  };

  return (
    <button
      type="button"
      onClick={handleToggle}
      className={`inline-flex h-10 w-10 items-center justify-center rounded-full border bg-white shadow-sm transition-all active:scale-[0.98] ${
        isMuted
          ? 'border-gray-300 text-gray-400'
          : 'border-[var(--color-primary-100)]/50 text-primary-100'
      } ${className}`}
      aria-label={isMuted ? '음소거 해제' : '음소거'}
      title={isMuted ? '음소거 해제' : '음소거'}
    >
      {isMuted ? <VolumeX size={17} strokeWidth={2.2} /> : <Volume2 size={17} strokeWidth={2.2} />}
    </button>
  );
}
