import { useState } from 'react';
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
import BusinessTypeStep from '@/features/auth/onboarding/steps/BusinessTypeStep.jsx';
import LocationStep from '@/features/auth/onboarding/steps/LocationStep.jsx';
import TimeStep from '@/features/auth/onboarding/steps/TimeStep.jsx';
import CompleteStep from '@/features/auth/onboarding/steps/CompleteStep.jsx';

function OnboardingPage() {
  const [step, setStep] = useState(1);

  const getProgressStep = (step) => {
    if (step <= 3) return 1;
    if (step <= 6) return 2;
    if (step === 7) return 3;
    if (step === 8) return 4;
    if (step <= 10) return 5;
    if (step <= 13) return 6;
    return 7;
  };

  const progressStep = getProgressStep(step);

  const [formData, setFormData] = useState({
    storeId: '',
    merchantId: '',
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
    isInstagramConnected: false,
  });

  const nextStep = () => setStep((prev) => prev + 1);
  const prevStep = () => setStep((prev) => prev - 1);

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
            onGoToQR={() => setStep(6)}
            onNext={() => setStep(7)}
          />
        );

      case 6:
        return <QRStep {...commonProps} onSuccess={nextStep} />;

      case 7:
        return <LoadingStep {...commonProps} />;

      case 8:
        return <PosSuccessStep {...commonProps} />;

      case 9:
        return <StoreSelectStep {...commonProps} />;

      case 10:
        return <StoreLoadingStep {...commonProps} />;

      case 11:
        return (
          <BusinessTypeStep
            {...commonProps}
            value={formData.category}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, category: value }))
            }
          />
        );

      case 12:
        return (
          <LocationStep
            {...commonProps}
            value={formData.naverPlaceId}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, naverPlaceId: value }))
            }
          />
        );

      case 13:
        return (
          <TimeStep
            {...commonProps}
            value={formData.operatingHours}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, operatingHours: value }))
            }
          />
        );

      case 14:
        return <CompleteStep progressStep={progressStep} />;

      default:
        return <div>잘못된 접근입니다</div>;
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6">
      {renderStep()}
    </main>
  );
}

export default OnboardingPage;
