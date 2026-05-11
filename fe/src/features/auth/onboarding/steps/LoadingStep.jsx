import { useEffect, useRef, useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import tossLoading from '@/assets/videos/toss-loading.mp4';
import { onboardingApi } from '@/features/auth/onboarding/api.js';

function LoadingStep({ onNext, onPrev, merchantId, onSynced }) {
  const hasSyncedRef = useRef(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!merchantId || hasSyncedRef.current) return;

    const syncStore = async () => {
      try {
        hasSyncedRef.current = true;
        setErrorMessage('');

        const response = await onboardingApi.syncPosStore(merchantId);
        const { success, storeId, message } = response.data;

        if (!success || !storeId) {
          setErrorMessage(message || 'POS 데이터 동기화에 실패했습니다.');
          return;
        }

        onSynced?.(storeId);
        onNext();
      } catch (error) {
        const message =
          error.response?.data?.message ||
          'POS 연결 중 오류가 발생했습니다. 다시 시도해 주세요.';

        setErrorMessage(message);
      }
    };

    syncStore();
  }, [merchantId, onNext, onSynced]);

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
        errorMessage ? (
          <OnboardingFooterButtons
            onPrev={onPrev}
            onNext={() => window.location.reload()}
            nextText="다시 시도"
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

        {errorMessage && (
          <p className="mt-4 text-sm font-medium text-red-500 text-center">
            {errorMessage}
          </p>
        )}
      </div>
    </OnboardingLayout>
  );
}

export default LoadingStep;
