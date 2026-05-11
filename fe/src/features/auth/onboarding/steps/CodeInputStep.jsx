import { useRef, useState } from 'react';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import { onboardingApi } from '@/features/auth/onboarding/api.js';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

function CodeInputStep({
  onNext,
  onPrev,
  value = '',
  onChange,
  onGoToQR,
  onVerified,
}) {
  const inputRefs = useRef([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState([]);

  const setMerchantId = useOnboardingStore((state) => state.setMerchantId);

  const handleChange = (e, idx) => {
    const val = e.target.value.replace(/[^0-9]/g, '');

    if (val.length > 1) return;

    const newValueArray = value.split('');
    newValueArray[idx] = val;
    const newValue = newValueArray.join('');

    onChange(newValue);
    setErrorMessage([]);

    if (val !== '' && idx < 5) {
      inputRefs.current[idx + 1]?.focus();
    }
  };

  const handleKeyDown = (e, idx) => {
    if (e.key === 'Backspace' && !value[idx] && idx > 0) {
      inputRefs.current[idx - 1]?.focus();
    }
  };

  const handleNext = async () => {
    if (isLoading) return;

    if (value.length !== 6) {
      setErrorMessage(['6자리 인증 코드를 입력해 주세요.']);
      return;
    }

    try {
      setIsLoading(true);
      setErrorMessage([]);

      const response = await onboardingApi.verifyPosPin(value);
      const { success, merchantId, message } = response.data;

      if (!success || !merchantId) {
        setErrorMessage([message || '인증 코드 검증에 실패했습니다.']);
        return;
      }

      setMerchantId(merchantId);
      onVerified?.(merchantId);
      onNext();
    } catch (error) {
      const message = error.response?.data?.message;

      setErrorMessage(
        message
          ? [message]
          : ['인증 코드 검증 중 오류가 발생했습니다.', '다시 시도해 주세요.']
      );
    } finally {
      setIsLoading(false);
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
          subtitle={
            <>
              토스 POS 기기 화면을 확인하신 뒤
              <br />
              6자리 숫자를 입력해 주세요.
            </>
          }
        />
      }
      footer={
        <OnboardingFooterButtons
          onPrev={onPrev}
          onNext={handleNext}
          nextText={isLoading ? '확인 중' : '다음'}
          nextDisabled={isLoading}
        />
      }
    >
      <div className="flex flex-col items-center mt-2 w-full">
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
              disabled={isLoading}
              className="w-12 h-14 border border-gray-300 rounded-xl text-center text-2xl font-bold text-gray-900 focus:outline-none focus:border-primary-100 focus:ring-4 focus:ring-primary-100/20 transition-all disabled:bg-gray-50"
            />
          ))}
        </div>

        {errorMessage.length > 0 && (
          <p className="mt-4 text-md font-medium text-red-500 text-center">
            {errorMessage.map((line) => (
              <span key={line} className="block">
                {line}
              </span>
            ))}
          </p>
        )}

        <button
          type="button"
          onClick={onGoToQR}
          disabled={isLoading}
          className="mt-8 text-lg text-gray-500 font-sm underline underline-offset-4 disabled:text-gray-300"
        >
          QR로 인증하기
        </button>

      </div>
    </OnboardingLayout>
  );
}

export default CodeInputStep;
