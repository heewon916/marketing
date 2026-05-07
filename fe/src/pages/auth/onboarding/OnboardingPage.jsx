import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import StartStep from '@/features/auth/onboarding/steps/StartStep.jsx';
import InstagramConnectStep from '@/features/auth/onboarding/steps/InstagramConnectStep.jsx';
import InstagramSuccessStep from '@/features/auth/onboarding/steps/InstagramSuccessStep.jsx';
import PosConnectStep from '@/features/auth/onboarding/steps/PosConnectStep.jsx';
import CodeInputStep from '@/features/auth/onboarding/steps/CodeInputStep.jsx';
import QRStep from '@/features/auth/onboarding/steps/QRStep.jsx';
import LoadingStep from '@/features/auth/onboarding/steps/LoadingStep.jsx';
import PosSuccessStep from '@/features/auth/onboarding/steps/PosSuccessStep.jsx';
import StoreSelectStep from '@/features/auth/onboarding/steps/StoreSelectStep.jsx';
import StoreLoadingStep from '@/features/auth/onboarding/steps/StoreLoadingStep.jsx';
import StoreNameStep from '@/features/auth/onboarding/steps/StoreNameStep.jsx';
import BusinessTypeStep from '@/features/auth/onboarding/steps/BusinessTypeStep.jsx';
import LocationStep from '@/features/auth/onboarding/steps/LocationStep.jsx';
import TimeStep from '@/features/auth/onboarding/steps/TimeStep.jsx';
import CompleteStep from '@/features/auth/onboarding/steps/CompleteStep.jsx';

import OnboardingLeaveConfirmModal from '@/features/auth/onboarding/components/OnboardingLeaveConfirmModal.jsx';

function OnboardingPage() {
  const navigate = useNavigate();

  const isInstagramSuccess =
    new URLSearchParams(window.location.search).get('instagram') === 'success';

  const [step, setStep] = useState(() => (isInstagramSuccess ? 3 : 1));
  const [, setStepHistory] = useState([]);
  const [isLeaveModalOpen, setIsLeaveModalOpen] = useState(false);

  const [formData, setFormData] = useState(() => ({
    storeId: '',
    merchantId: '',
    storeName: '',
    category: '',
    ownerPersona: '',
    aesthetic: '',
    naverPlaceId: '',
    address: '',
    lat: null,
    lng: null,
    operatingHours: {},
    menus: [],
    authCode: '',
    isInstagramConnected: isInstagramSuccess,
  }));

  const getProgressStep = (step) => {
    if (step <= 3) return 1;
    if (step <= 6) return 2;
    if (step === 7) return 3;
    if (step === 8) return 4;
    if (step <= 10) return 5;
    if (step <= 14) return 6;
    return 7;
  };

  const progressStep = getProgressStep(step);

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

  const moveToStep = (nextStep) => {
    setStepHistory((prev) => [...prev, step]);
    setStep(nextStep);
  };

  const nextStep = () => {
    moveToStep(step + 1);
  };

  const prevStep = () => {
    setStepHistory((prev) => {
      if (prev.length === 0) {
        navigate('/', { replace: true });
        return prev;
      }

      const previousStep = prev[prev.length - 1];

      setStep(previousStep);

      return prev.slice(0, -1);
    });
  };

  const handleCancelLeave = () => {
    setIsLeaveModalOpen(false);
  };

  const handleConfirmLeave = () => {
    setIsLeaveModalOpen(false);
    navigate('/', { replace: true });
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
        return (
          <InstagramConnectStep
            {...commonProps}
            setFormData={setFormData}
          />
        );

      case 3:
        return <InstagramSuccessStep {...commonProps} />;

      case 4:
        return <PosConnectStep {...commonProps} />;

      case 5:
        return (
          <CodeInputStep
            {...commonProps}
            value={formData.authCode}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, authCode: value }))
            }
            onGoToQR={() => moveToStep(6)}
            onNext={() => moveToStep(7)}
          />
        );

      case 6:
        return <QRStep {...commonProps} onSuccess={nextStep} />;

      case 7:
        return <LoadingStep {...commonProps} />;

      case 8:
        return <PosSuccessStep {...commonProps} />;

      case 9:
        return (
          <StoreSelectStep
            {...commonProps}
            onManualInput={() => moveToStep(11)}
          />
        );

      case 10:
        return <StoreLoadingStep {...commonProps} />;

      case 11:
        return (
          <StoreNameStep
            {...commonProps}
            value={formData.storeName}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, storeName: value }))
            }
          />
        );

      case 12:
        return (
          <BusinessTypeStep
            {...commonProps}
            value={formData.category}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, category: value }))
            }
          />
        );

      case 13:
        return (
          <LocationStep
            {...commonProps}
            value={formData.naverPlaceId}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, naverPlaceId: value }))
            }
          />
        );

      case 14:
        return (
          <TimeStep
            {...commonProps}
            value={formData.operatingHours}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, operatingHours: value }))
            }
          />
        );

      case 15:
        return <CompleteStep progressStep={progressStep} />;

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
    </>
  );
}

export default OnboardingPage;
