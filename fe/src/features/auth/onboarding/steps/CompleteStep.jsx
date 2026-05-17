import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '@/components/common/Button.jsx';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import CharacterLove from '@/assets/character/CharacterLove.png';
import CharacterRun from '@/assets/character/CharacterRun.png';
import CharacterFail from '@/assets/character/CharacterFail.png';
import { onboardingApi } from '@/features/auth/onboarding/api.js';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

const MIN_SAVING_TIME = 2000;

const ONBOARDING_SAVE_ERROR_MESSAGE =
  '온보딩 정보를 저장하는 중 오류가 발생했습니다.';
const STORE_INFO_MISSING_MESSAGE =
  '가게 정보가 없습니다.';

const wait = (ms) =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });

const waitRemainingTime = async (startedAt) => {
  const elapsedTime = Date.now() - startedAt;
  const remainingTime = Math.max(MIN_SAVING_TIME - elapsedTime, 0);

  if (remainingTime > 0) {
    await wait(remainingTime);
  }
};

function CompleteStep({ onPrev, onRestartPos, onStatusChange }) {
  const navigate = useNavigate();
  const hasSubmittedRef = useRef(false);

  const [count, setCount] = useState(3);
  const [status, setStatus] = useState('saving');
  const [errorMessage, setErrorMessage] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    onStatusChange?.(status);
  }, [status, onStatusChange]);

  const storeId = useOnboardingStore((state) => state.storeId);
  const getOnboardingPayload = useOnboardingStore(
    (state) => state.getOnboardingPayload
  );
  const resetOnboarding = useOnboardingStore(
    (state) => state.resetOnboarding
  );

  const displayErrorMessage = errorMessage;

  useEffect(() => {
    if (!storeId) {
      setStatus('error');
      setErrorMessage(STORE_INFO_MISSING_MESSAGE);
      return;
    }

    if (hasSubmittedRef.current) return;

    const completeOnboarding = async () => {
      const startedAt = Date.now();

      try {
        hasSubmittedRef.current = true;

        const payload = getOnboardingPayload();
        const response = await onboardingApi.completeOnboarding(
          storeId,
          payload
        );

        const { success, message } = response.data;

        await waitRemainingTime(startedAt);

        if (!success) {
          setStatus('error');
          setErrorMessage(message || ONBOARDING_SAVE_ERROR_MESSAGE);
          return;
        }

        setStatus('success');
        setErrorMessage('');
      } catch (error) {
        await waitRemainingTime(startedAt);

        const message =
          error.response?.data?.message || ONBOARDING_SAVE_ERROR_MESSAGE;

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

  const handleGoPrev = () => {
    setErrorMessage('');
    onPrev?.();
  };

  const handleRestartPos = () => {
    hasSubmittedRef.current = false;
    setStatus('saving');
    setErrorMessage('');
    setCount(3);
    setRetryCount((prev) => prev + 1);

    resetOnboarding();
    onRestartPos?.();
  };

  const isSuccess = status === 'success';
  const isError = status === 'error' || !!displayErrorMessage;
  const isSaving = status === 'saving' && !isError;

  const characterImage = isSuccess
    ? CharacterLove
    : isError
      ? CharacterFail
      : CharacterRun;

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
              ) : isError ? (
                <>
                  온보딩 정보를
                  <br />
                  <span className="text-primary-100 font-extrabold">
                    저장하지 못했어요
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
            isSuccess ? (
              '잠시 후 메인 페이지로 이동합니다'
            ) : isError ? (
              <>
                POS 연결부터 다시 시도하거나
                <br />
                이전 단계로 돌아갈 수 있어요
              </>
            ) : (
              '잠시만 기다려 주세요'
            )
          }
        />
      }
      footer={
        isError ? (
          <div className="flex w-full gap-3">
            <Button
              type="button"
              variant="white"
              size="sm"
              onClick={handleGoPrev}
              className="flex-1 font-bold whitespace-nowrap"
            >
              이전
            </Button>

            <Button
              type="button"
              size="sm"
              onClick={handleRestartPos}
              className="flex-1 text-[18px] font-bold whitespace-nowrap"
            >
              다시하기
            </Button>
          </div>
        ) : null
      }
    >
      <div className="w-full flex justify-center mt-10">
        <img
          src={characterImage}
          alt="character"
          className="w-full max-w-[320px]"
        />
      </div>

      {isSuccess && (
        <div className="mt-8 text-4xl font-extrabold text-primary-100">
          {count}
        </div>
      )}

      {isSaving && (
        <p className="mt-8 text-base font-medium text-gray-400">
          온보딩 정보를 저장하고 있어요.
        </p>
      )}
    </OnboardingLayout>
  );
}

export default CompleteStep;
