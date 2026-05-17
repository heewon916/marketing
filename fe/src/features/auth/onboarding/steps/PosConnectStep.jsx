import { useEffect, useRef } from 'react';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import Character from '@/assets/character/CharacterIdea.mp4';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';

function PosConnectStep({ onNext, onPrev }) {
  const videoRef = useRef(null);

  useEffect(() => {
    if (!videoRef.current) return;

    videoRef.current.playbackRate = 1.3;
  }, []);

  return (
    <OnboardingLayout
      currentStep={3}
      totalStep={7}
      contentAlign="left"
      header={
        <OnboardingHeader
          title={
            <>
              가게 정보를 가져오기 위해
              <br />
              <span className="text-primary-100 font-extrabold">
                토스 POS를 연결
              </span>
              할게요
            </>
          }
        />
      }
      footer={
        <OnboardingFooterButtons
          onPrev={onPrev}
          onNext={onNext}
        />
      }
    >
      <div className="w-full flex justify-center mt-10">
        <video
          ref={videoRef}
          src={Character}
          className="w-full max-w-[320px]"
          autoPlay
          loop
          muted
          playsInline
        />
      </div>
    </OnboardingLayout>
  );
}

export default PosConnectStep;
