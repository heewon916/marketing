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

function OnboardingPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const setMerchantId = useOnboardingStore((state) => state.setMerchantId);

  const isInstagramSuccess =
    new URLSearchParams(window.location.search).get('instagram') === 'success';

  const authNotice = location.state?.authNotice ?? null;
  const authRedirectTo = location.state?.redirectTo ?? null;
  const hasAuthNotice = !!authNotice;

  const [step, setStep] = useState(() =>
    isInstagramSuccess && !hasAuthNotice ? 3 : 1
  );
  const [stepHistory, setStepHistory] = useState([]);
  const [isLeaveModalOpen, setIsLeaveModalOpen] = useState(false);
  const [authCode, setAuthCode] = useState('');

  useEffect(() => {
    if (isInstagramSuccess) {
      window.history.replaceState({}, document.title, '/auth/onboarding');
    }
  }, [isInstagramSuccess]);

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
        return <LoadingStep {...commonProps} />;

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
