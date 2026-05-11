import { useEffect, useRef, useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import tossLoading from '@/assets/videos/toss-loading.mp4';
import { onboardingApi } from '@/features/auth/onboarding/api.js';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

function LoadingStep({ onNext, onPrev }) {
  const hasSyncedRef = useRef(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const merchantId = useOnboardingStore((state) => state.merchantId);
  const setPosSyncResult = useOnboardingStore(
    (state) => state.setPosSyncResult
  );

  const displayErrorMessage =
    errorMessage ||
    (!merchantId ? 'POS 인증 정보가 없습니다. 다시 인증해 주세요.' : '');

  useEffect(() => {
    if (!merchantId || hasSyncedRef.current) return;

    const syncStore = async () => {
      try {
        hasSyncedRef.current = true;
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

        if (!success || !storeId) {
          setErrorMessage(message || 'POS 데이터 동기화에 실패했습니다.');
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
        const message =
          error.response?.data?.message ||
          'POS 연결 중 오류가 발생했습니다. 다시 시도해 주세요.';

        setErrorMessage(message);
      }
    };

    void syncStore();
  }, [merchantId, onNext, setPosSyncResult, retryCount]);

  const handleRetry = () => {
    hasSyncedRef.current = false;
    setErrorMessage('');
    setRetryCount((prev) => prev + 1);
  };

  return (
    <OnboardingLayout
      currentStep={3}
      totalStep={7}
      header={
        <OnboardingHeader
          title={
            <>
              토스 POS와
              <br />
              연결하고 있어요
            </>
          }
        />
      }
      footer={
        displayErrorMessage ? (
          <OnboardingFooterButtons
            onPrev={onPrev}
            onNext={merchantId ? handleRetry : onPrev}
            nextText={merchantId ? '다시 시도' : '인증 다시 하기'}
          />
        ) : null
      }
    >
      <div className="flex flex-col items-center w-full">
        <video
          src={tossLoading}
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full justify-center object-contain"
        />

        {displayErrorMessage && (
          <p className="mt-4 text-sm font-medium text-red-500 text-center">
            {displayErrorMessage}
          </p>
        )}
      </div>
    </OnboardingLayout>
  );
}

export default LoadingStep;
