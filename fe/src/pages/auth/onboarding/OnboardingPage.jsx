import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Modal from '@/components/common/Modal.jsx';
import Button from '@/components/common/Button.jsx';

import StartStep from '@/features/auth/onboarding/steps/StartStep.jsx';
import InstagramConnectStep from '@/features/auth/onboarding/steps/InstagramConnectStep.jsx';
import InstagramSuccessStep from '@/features/auth/onboarding/steps/InstagramSuccessStep.jsx';
import PosConnectStep from '@/features/auth/onboarding/steps/PosConnectStep.jsx';
import PosCodeInputStep from '@/features/auth/onboarding/steps/PosCodeInputStep.jsx';
import QRStep from '@/features/auth/onboarding/steps/QRStep.jsx';
import LoadingStep from '@/features/auth/onboarding/steps/LoadingStep.jsx';
import PosSuccessStep from '@/features/auth/onboarding/steps/PosSuccessStep.jsx';
import StoreSelectStep from '@/features/auth/onboarding/steps/StoreSelectStep.jsx';
import StoreLoadingStep from '@/features/auth/onboarding/steps/StoreLoadingStep.jsx';
import StoreSearchFailStep from '@/features/auth/onboarding/steps/StoreSearchFailStep.jsx';
import StoreNameStep from '@/features/auth/onboarding/steps/StoreNameStep.jsx';
import BusinessTypeStep from '@/features/auth/onboarding/steps/BusinessTypeStep.jsx';
import LocationStep from '@/features/auth/onboarding/steps/LocationStep.jsx';
import TimeStep from '@/features/auth/onboarding/steps/TimeStep.jsx';
import CompleteStep from '@/features/auth/onboarding/steps/CompleteStep.jsx';

import OnboardingLeaveConfirmModal from '@/features/auth/onboarding/components/OnboardingLeaveConfirmModal.jsx';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';
import { speak, stopTTS } from '@/utils/tts';
import onboardingCase2TTS from '@/assets/TTS/on_boarding_case2_TTS.mp3';
import onboardingCase3TTS from '@/assets/TTS/on_boarding_case3_TTS.mp3';
import onboardingCase4TTS from '@/assets/TTS/on_boarding_case4_TTS.mp3';
import onboardingCase8TTS from '@/assets/TTS/on_boarding_case8_TTS.mp3';
import onboardingCase7ErrorTTS from '@/assets/TTS/on_boarding_case7_error_TTS.mp3';
import onboardingCase9TTS from '@/assets/TTS/on_boarding_case9_TTS.mp3';
import onboardingCase11TTS from '@/assets/TTS/on_boarding_case11_TTS.mp3';
import onboardingCase16TTS from '@/assets/TTS/on_boarding_case16_TTS.mp3';
import onboardingCase16ErrorTTS from '@/assets/TTS/on_boarding_case16_error_TTS.mp3';

const ONBOARDING_TTS_BY_STEP = {
  2: onboardingCase2TTS,
  3: onboardingCase3TTS,
  4: onboardingCase4TTS,
  8: onboardingCase8TTS,
  9: onboardingCase9TTS,
  11: onboardingCase11TTS,
};

const ONBOARDING_CASE16_TTS_BY_STATUS = {
  success: onboardingCase16TTS,
  error: onboardingCase16ErrorTTS,
};

const ONBOARDING_CASE7_ERROR_TTS = onboardingCase7ErrorTTS;

function OnboardingPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const setMerchantId = useOnboardingStore((state) => state.setMerchantId);

  const isInstagramSuccess =
    new URLSearchParams(location.search).get('instagram') === 'success';
  const authNotice = location.state?.authNotice ?? null;
  const authRedirectTo = location.state?.redirectTo ?? null;
  const hasAuthNotice = !!authNotice;

  const [step, setStep] = useState(() =>
    isInstagramSuccess && !authNotice ? 3 : 1
  );
  const [stepHistory, setStepHistory] = useState([]);
  const [isLeaveModalOpen, setIsLeaveModalOpen] = useState(false);
  const [authCode, setAuthCode] = useState('');
  const [loadingStepStatus, setLoadingStepStatus] = useState('loading');
  const [completeStepStatus, setCompleteStepStatus] = useState('saving');

  useEffect(() => {
    if (!isInstagramSuccess || hasAuthNotice) return;

    navigate(location.pathname, {
      replace: true,
      state: location.state ?? null,
    });
  }, [
    hasAuthNotice,
    isInstagramSuccess,
    location.pathname,
    location.state,
    navigate,
  ]);

  useEffect(() => {
    window.history.pushState({ onboardingGuard: true }, '');

    const handlePopState = () => {
      setIsLeaveModalOpen(true);
      window.history.pushState({ onboardingGuard: true }, '');
    };

    window.addEventListener('popstate', handlePopState);

    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  // 스텝 진입 시 고정 TTS (case 16은 상태별로 별도 처리)
  useEffect(() => {
    if (step === 16) return;

    const audioSrc = ONBOARDING_TTS_BY_STEP[step];

    if (!audioSrc) {
      stopTTS();
      return;
    }

    void speak('', {
      source: 'file',
      audioSrc,
      fallbackToTTS: false,
    });
  }, [step]);

  // case 7: 에러 상태 전환 시 TTS
  useEffect(() => {
    if (step !== 7 || loadingStepStatus !== 'error') return;
    void speak('', { source: 'file', audioSrc: ONBOARDING_CASE7_ERROR_TTS, fallbackToTTS: false });
  }, [step, loadingStepStatus]);

  // case 16: 상태별 TTS
  useEffect(() => {
    if (step !== 16) return;

    const audioSrc = ONBOARDING_CASE16_TTS_BY_STATUS[completeStepStatus];
    if (!audioSrc) return;

    void speak('', {
      source: 'file',
      audioSrc,
      fallbackToTTS: false,
    });
  }, [step, completeStepStatus]);

  useEffect(() => {
    return () => {
      stopTTS();
    };
  }, []);

  const getProgressStep = (currentStep) => {
    if (currentStep <= 3) return 1;
    if (currentStep <= 6) return 2;
    if (currentStep === 7) return 3;
    if (currentStep === 8) return 4;
    if (currentStep <= 13) return 5;
    if (currentStep <= 15) return 6;
    return 7;
  };

  const progressStep = getProgressStep(step);

  const moveToStep = (nextStep) => {
    setStepHistory((prev) => [...prev, step]);
    setStep(nextStep);
  };

  const nextStep = () => {
    moveToStep(step + 1);
  };

  const prevStep = () => {
    if (stepHistory.length === 0) {
      navigate('/', { replace: true });
      return;
    }

    const previousStep = stepHistory[stepHistory.length - 1];

    setStep(previousStep);
    setStepHistory((prev) => prev.slice(0, -1));
  };

  const handleCancelLeave = () => {
    setIsLeaveModalOpen(false);
  };

  const handleConfirmLeave = () => {
    setIsLeaveModalOpen(false);
    navigate('/', { replace: true });
  };

  const handleCloseAuthNoticeModal = () => {
    if (authRedirectTo) {
      navigate(authRedirectTo, { replace: true });
      return;
    }

    navigate(location.pathname, {
      replace: true,
      state: null,
    });
  };

  const handleVerified = (merchantId) => {
    setMerchantId(merchantId);
  };

  const commonProps = {
    onNext: nextStep,
    onPrev: prevStep,
    progressStep,
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return <StartStep {...commonProps} />;

      case 2:
        return <InstagramConnectStep {...commonProps} />;

      case 3:
        return <InstagramSuccessStep {...commonProps} />;

      case 4:
        return <PosConnectStep {...commonProps} />;

      case 5:
        return (
          <PosCodeInputStep
            {...commonProps}
            value={authCode}
            onChange={setAuthCode}
            onVerified={handleVerified}
            onGoToQR={() => moveToStep(6)}
            onNext={() => moveToStep(7)}
          />
        );

      case 6:
        return (
          <QRStep
            {...commonProps}
            onSuccess={() => moveToStep(7)}
            onVerified={handleVerified}
          />
        );

      case 7:
        return <LoadingStep {...commonProps} onStatusChange={setLoadingStepStatus} />;

      case 8:
        return (
          <PosSuccessStep
            {...commonProps}
            onNext={() => moveToStep(9)}
          />
        );

      case 9:
        return (
          <StoreLoadingStep
            {...commonProps}
            onSearchSuccess={() => moveToStep(10)}
            onSearchFail={() => moveToStep(11)}
          />
        );

      case 10:
        return (
          <StoreSelectStep
            {...commonProps}
            onNext={() => moveToStep(14)}
            onManualInput={() => moveToStep(12)}
            onSearchFail={() => moveToStep(11)}
          />
        );

      case 11:
        return (
          <StoreSearchFailStep
            {...commonProps}
            onNext={() => moveToStep(12)}
          />
        );

      case 12:
        return (
          <StoreNameStep
            {...commonProps}
            onSearchSuccess={() => moveToStep(10)}
            onSearchFail={() => moveToStep(13)}
          />
        );

      case 13:
        return <BusinessTypeStep {...commonProps} />;

      case 14:
        return <LocationStep {...commonProps} />;

      case 15:
        return <TimeStep {...commonProps} />;

      case 16:
        return (
          <CompleteStep
            {...commonProps}
            onRestartPos={() => moveToStep(4)}
            onStatusChange={setCompleteStepStatus}
          />
        );

      default:
        return <div>잘못된 접근입니다</div>;
    }
  };

  return (
    <>
      <main className="flex min-h-screen flex-col items-center justify-center px-6">
        {renderStep()}
      </main>

      <OnboardingLeaveConfirmModal
        isOpen={isLeaveModalOpen}
        onCancel={handleCancelLeave}
        onConfirm={handleConfirmLeave}
      />

      <Modal
        isOpen={hasAuthNotice}
        onClose={handleCloseAuthNoticeModal}
        showClose={false}
        closeOnBackdrop={false}
      >
        <div className="text-center">
          <h3 className="text-xl font-bold text-gray-900">
            {authNotice?.title}
          </h3>

          <p className="mt-4 text-base leading-6 text-gray-500 whitespace-pre-line">
            {authNotice?.description}
          </p>

          <Button
            onClick={handleCloseAuthNoticeModal}
            className="mt-8 w-full font-bold"
          >
            확인
          </Button>
        </div>
      </Modal>
    </>
  );
}

export default OnboardingPage;
