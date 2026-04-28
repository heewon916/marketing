import { useState } from 'react';
import StartStep from '@/features/auth/onboarding/steps/StartStep.jsx';
import InstagramConnectStep from '@/features/auth/onboarding/steps/InstagramConnectStep.jsx';
import InstagramLoginStep from '@/features/auth/onboarding/steps/InstagramLoginStep.jsx';
import InstagramSuccessStep from '@/features/auth/onboarding/steps/InstagramSuccessStep.jsx';
import PosConnectStep from '@/features/auth/onboarding/steps/PosConnectStep.jsx';
import CodeInputStep from '@/features/auth/onboarding/steps/CodeInputStep.jsx';
import QRStep from '@/features/auth/onboarding/steps/QRStep.jsx';
import LoadingStep from '@/features/auth/onboarding/steps/LoadingStep.jsx';
import StoreSelectStep from '@/features/auth/onboarding/steps/StoreSelectStep.jsx';
import BusinessNameStep from '@/features/auth/onboarding/steps/BusinessNameStep.jsx';
import BusinessTypeStep from '@/features/auth/onboarding/steps/BusinessTypeStep.jsx';
import LocationStep from '@/features/auth/onboarding/steps/LocationStep.jsx';
import TimeStep from '@/features/auth/onboarding/steps/TimeStep.jsx';
import CompleteStep from '@/features/auth/onboarding/steps/CompleteStep.jsx';

function OnboardingPage() {
  const [step, setStep] = useState(1);

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
    storeName: '',
    operatingHours: {},
    menus: [],
    authCode: '',
  });

  const nextStep = () => setStep((prev) => prev + 1);
  const prevStep = () => setStep((prev) => prev - 1);

  const renderStep = () => {
    switch (step) {
      case 1:
        return <StartStep onNext={nextStep} />;

      case 2:
        return <InstagramConnectStep onNext={nextStep} onPrev={prevStep} />;

      case 3:
        return <InstagramLoginStep onNext={nextStep} onPrev={prevStep} />;

      case 4:
        return <InstagramSuccessStep onNext={nextStep} />;

      case 5:
        return <PosConnectStep onNext={nextStep} onPrev={prevStep} />;

      case 6:
        return (
          <CodeInputStep
            onNext={nextStep}
            onPrev={prevStep}
            value={formData.authCode}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, authCode: value }))
            }
          />
        );

      case 7:
        return <QRStep onNext={nextStep} onPrev={prevStep} />;

      case 8:
        return <LoadingStep onNext={nextStep} />;

      case 9:
        return <StoreSelectStep onNext={nextStep} onPrev={prevStep} />;

      case 10:
        return (
          <BusinessNameStep
            onNext={nextStep}
            onPrev={prevStep}
            value={formData.storeName}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, storeName: value }))
            }
          />
        );

      case 11:
        return (
          <BusinessTypeStep
            onNext={nextStep}
            onPrev={prevStep}
            value={formData.category}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, category: value }))
            }
          />
        );

      case 12:
        return (
          <LocationStep
            onNext={nextStep}
            onPrev={prevStep}
            value={formData.naverPlaceId}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, naverPlaceId: value }))
            }
          />
        );

      case 13:
        return (
          <TimeStep
            onNext={nextStep}
            onPrev={prevStep}
            value={formData.operatingHours}
            onChange={(value) =>
              setFormData((prev) => ({ ...prev, operatingHours: value }))
            }
          />
        );

      case 14:
        return <CompleteStep />;

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
