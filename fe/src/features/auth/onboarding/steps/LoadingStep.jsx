import { useEffect, useRef, useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import tossLoading from '@/assets/videos/toss-loading.mp4';
import CharacterFail from '@/assets/character/CharacterFail.mp4';
import { onboardingApi } from '@/features/auth/onboarding/api.js';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

const MIN_LOADING_TIME = 2000;

const POS_SYNC_ERROR_MESSAGE =
  'POS 연결 중 오류가 발생했습니다.\n다시 시도해 주세요.';

const wait = (ms) =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });

const waitRemainingTime = async (startedAt) => {
  const elapsedTime = Date.now() - startedAt;
  const remainingTime = Math.max(MIN_LOADING_TIME - elapsedTime, 0);

  if (remainingTime > 0) {
    await wait(remainingTime);
  }
};

function LoadingStep({ onNext, onPrev }) {
  const hasSyncedRef = useRef(false);
  const [status, setStatus] = useState('loading');
  const [errorMessage, setErrorMessage] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const merchantId = useOnboardingStore((state) => state.merchantId);
  const setPosSyncResult = useOnboardingStore(
    (state) => state.setPosSyncResult
  );

  const displayErrorMessage =
    errorMessage ||
    (!merchantId ? 'POS 인증 정보가 없습니다.\n다시 인증해 주세요.' : '');

  useEffect(() => {
    if (!merchantId || hasSyncedRef.current) return;

    const syncStore = async () => {
      const startedAt = Date.now();

      try {
        hasSyncedRef.current = true;
        setStatus('loading');
        setErrorMessage('');

        const response = await onboardingApi.syncPosStore(merchantId);
        const {
          success,
          storeId,
          storeName,
          suggestedCategory,
          menus,
          message,
        } = response.data;

        await waitRemainingTime(startedAt);

        if (!success || !storeId) {
          setStatus('error');
          setErrorMessage(message || POS_SYNC_ERROR_MESSAGE);
          return;
        }

        setPosSyncResult({
          storeId,
          storeName,
          suggestedCategory,
          menus,
        });

        onNext();
      } catch (error) {
        await waitRemainingTime(startedAt);

        const message =
          error.response?.data?.message || POS_SYNC_ERROR_MESSAGE;

        setStatus('error');
        setErrorMessage(message);
      }
    };

    void syncStore();
  }, [merchantId, onNext, setPosSyncResult, retryCount]);

  const handleRetry = () => {
    if (!merchantId) {
      onPrev?.();
      return;
    }

    hasSyncedRef.current = false;
    setStatus('loading');
    setErrorMessage('');
    setRetryCount((prev) => prev + 1);
  };

  const isError = status === 'error' || !!displayErrorMessage;

  return (
    <OnboardingLayout
      currentStep={3}
      totalStep={7}
      contentAlign="center"
      header={
        <OnboardingHeader
          title={
            isError ? (
              <>
                토스 POS와
                <br />
                <span className="text-primary-100 font-extrabold">
                  연결하지 못했어요
                </span>
              </>
            ) : (
              <>
                토스 POS와
                <br />
                <span className="text-primary-100 font-extrabold">
                  연결하고 있어요
                </span>
              </>
            )
          }
          subtitle={
            isError
              ? '다시 시도하거나 이전 단계로 돌아갈 수 있어요'
              : '잠시만 기다려 주세요'
          }
        />
      }
      footer={
        isError ? (
          <>
          <OnboardingFooterButtons
            onPrev={onPrev}
            onNext={merchantId ? handleRetry : onPrev}
            nextText={merchantId ? '다시 시도' : '인증 다시 하기'}
          />
          {import.meta.env.DEV && (
            <button
              type="button"
              onClick={onNext}
              className="mt-3 text-sm font-medium text-gray-400 underline"
            >
              개발용: 인스타그램 연동 건너뛰기
            </button>
          )}
        </>
        ) : null
      }
    >
      <div className="flex flex-col items-center w-full">
        {isError ? (
          <video
            src={CharacterFail}
            autoPlay
            loop
            muted
            playsInline
            className="mt-10 w-full max-w-[320px]"
          />
        ) : (
          <video
            src={tossLoading}
            autoPlay
            loop
            muted
            playsInline
            className="w-full h-full justify-center object-contain outline-none border-none shadow-none isolate"
            style={{
              transform: 'translateZ(0)',
              backfaceVisibility: 'hidden',
              WebkitBackfaceVisibility: 'hidden',
              willChange: 'auto',
              WebkitTapHighlightColor: 'transparent',
              WebkitTouchCallout: 'none',
              contain: 'paint'
            }}
          />
        )}

        {!isError && (
          <p className="mt-8 text-base font-medium text-gray-400">
            가게 정보를 불러오고 있어요.
          </p>
        )}

      </div>
    </OnboardingLayout>
  );
}

export default LoadingStep;
