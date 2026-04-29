import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import Character from '@/assets/character/CharacterLove.png';

function CompleteStep() {
  const [count, setCount] = useState(3);
  const navigate = useNavigate();

  useEffect(() => {
    if (count === 0) {
      navigate('/home');
      return;
    }

    const timer = setInterval(() => {
      setCount((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [count, navigate]);

  return (
    <OnboardingLayout
      currentStep={7}
      totalStep={7}
      contentAlign="center"
      header={
        <OnboardingHeader
          title={
            <>
              모든 연동이
              <br />
              <span className="text-primary-100 font-extrabold">
                완료되었어요!
              </span>
            </>
          }
          subtitle="잠시 후 메인 페이지로 이동합니다"
        />
      }
    >
      {/* 캐릭터 */}
      <div className="w-full flex justify-center mt-10">
        <img
          src={Character}
          alt="character"
          className="w-full max-w-[320px]"
        />
      </div>

      {/* 카운트다운 */}
      <div className="mt-8 text-4xl font-extrabold text-primary-100">
        {count}
      </div>
    </OnboardingLayout>
  );
}

export default CompleteStep;