import { useRef } from 'react';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';

function CodeInputStep({ onNext, onPrev, value = '', onChange, onGoToQR }) {
  const inputRefs = useRef([]);

  const handleChange = (e, idx) => {
    const val = e.target.value.replace(/[^0-9]/g, '');
    
    if (val.length > 1) return;

    const newValueArray = value.split('');
    newValueArray[idx] = val;
    const newValue = newValueArray.join('');
    
    onChange(newValue);

    if (val !== '' && idx < 5) {
      inputRefs.current[idx + 1].focus();
    }
  };

  const handleKeyDown = (e, idx) => {
    if (e.key === 'Backspace' && !value[idx] && idx > 0) {
      inputRefs.current[idx - 1].focus();
    }
  };

  return (
    <OnboardingLayout
      currentStep={3}
      totalStep={7}
      contentAlign="center"
      header={
        <OnboardingHeader
          title={
            <>
              POS 화면에 보이는
              <br />
              <span className="text-primary-100 font-extrabold">
                인증 코드를 입력
              </span>
              해 주세요
            </>
          }
          subtitle="토스 POS 기기에 표시된 6자리 숫자를 입력하세요"
        />
      }
      footer={
        <OnboardingFooterButtons
          onPrev={onPrev}
          onNext={onNext}
        />
      }
    >
      <div className="flex flex-col items-center mt-2 w-full">
        {/* 인증 코드 입력 영역 */}
        <div className="flex gap-2 justify-center">
          {Array.from({ length: 6 }).map((_, idx) => (
            <input
              key={idx}
              ref={(el) => (inputRefs.current[idx] = el)}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={value[idx] || ''}
              onChange={(e) => handleChange(e, idx)}
              onKeyDown={(e) => handleKeyDown(e, idx)}
              className="w-12 h-14 border border-gray-300 rounded-xl text-center text-2xl font-bold text-gray-900 focus:outline-none focus:border-primary-100 focus:ring-4 focus:ring-primary-100/20 transition-all"
            />
          ))}
        </div>

        {/* QR 인증 이동 버튼 */}
        <button 
          onClick={onGoToQR} 
          className="mt-8 text-lg text-gray-500 font-sm underline underline-offset-4 "
        >
          QR로 인증하기
        </button>
      </div>
    </OnboardingLayout>
  );
}

export default CodeInputStep;
