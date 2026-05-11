import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import Character from '@/assets/character/CharacterLove.png';
import { onboardingApi } from '@/features/auth/onboarding/api.js';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

function CompleteStep() {
  const navigate = useNavigate();
  const hasSubmittedRef = useRef(false);

  const [count, setCount] = useState(3);
  const [status, setStatus] = useState('saving');
  const [errorMessage, setErrorMessage] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const storeId = useOnboardingStore((state) => state.storeId);
  const getOnboardingPayload = useOnboardingStore(
    (state) => state.getOnboardingPayload
  );
  const resetOnboarding = useOnboardingStore(
    (state) => state.resetOnboarding
  );

  const displayErrorMessage =
    errorMessage ||
    (!storeId ? '가게 정보가 없습니다. POS 연결부터 다시 진행해 주세요.' : '');

  useEffect(() => {
    if (!storeId || hasSubmittedRef.current) return;

    const completeOnboarding = async () => {
      try {
        hasSubmittedRef.current = true;

        const payload = getOnboardingPayload();
        const response = await onboardingApi.completeOnboarding(
          storeId,
          payload
        );

        const { success, message } = response.data;

        if (!success) {
          setStatus('error');
          setErrorMessage(message || '온보딩 최종 저장에 실패했습니다.');
          return;
        }

        setStatus('success');
        setErrorMessage('');
      } catch (error) {
        const message =
          error.response?.data?.message ||
          '온보딩 정보를 저장하는 중 오류가 발생했습니다. 다시 시도해 주세요.';

        setStatus('error');
        setErrorMessage(message);
      }
    };

    void completeOnboarding();
  }, [storeId, getOnboardingPayload, retryCount]);

  useEffect(() => {
    if (status !== 'success') return;

    if (count === 0) {
      resetOnboarding();
      navigate('/home', { replace: true });
      return;
    }

    const timer = setInterval(() => {
      setCount((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [status, count, navigate, resetOnboarding]);

  const handleRetry = () => {
    hasSubmittedRef.current = false;
    setStatus('saving');
    setErrorMessage('');
    setCount(3);
    setRetryCount((prev) => prev + 1);
  };

  const isSuccess = status === 'success';
  const isError = !!displayErrorMessage || status === 'error';

  return (
    <OnboardingLayout
      currentStep={7}
      totalStep={7}
      contentAlign="center"
      header={
        <OnboardingHeader
          title={
            <>
              {isSuccess ? (
                <>
                  모든 연동이
                  <br />
                  <span className="text-primary-100 font-extrabold">
                    완료되었어요!
                  </span>
                </>
              ) : (
                <>
                  온보딩 정보를
                  <br />
                  <span className="text-primary-100 font-extrabold">
                    저장하고 있어요
                  </span>
                </>
              )}
            </>
          }
          subtitle={
            isSuccess
              ? '잠시 후 메인 페이지로 이동합니다'
              : '잠시만 기다려 주세요'
          }
        />
      }
      footer={
        isError ? (
          <OnboardingFooterButtons
            onPrev={() => navigate('/auth/onboarding', { replace: true })}
            onNext={storeId ? handleRetry : () => navigate('/auth/onboarding', { replace: true })}
            nextText={storeId ? '다시 시도' : '처음부터 다시 하기'}
          />
        ) : null
      }
    >
      <div className="w-full flex justify-center mt-10">
        <img
          src={Character}
          alt="character"
          className="w-full max-w-[320px]"
        />
      </div>

      {isSuccess && (
        <div className="mt-8 text-4xl font-extrabold text-primary-100">
          {count}
        </div>
      )}

      {displayErrorMessage && (
        <p className="mt-6 text-sm font-medium text-red-500 text-center whitespace-pre-line">
          {displayErrorMessage}
        </p>
      )}
    </OnboardingLayout>
  );
}

export default CompleteStep;
