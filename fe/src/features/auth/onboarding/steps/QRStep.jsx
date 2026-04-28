import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingBackButton from '../components/OnboardingBackButton.jsx';

function QRStep({ onPrev }) {
  return (
    <OnboardingLayout
      currentStep={3}
      totalStep={7}
      header={
        <OnboardingHeader
          title={
            <>
              사각형 안에
              <br />
              <span className="text-primary-100 font-extrabold">QR</span>이 오도록 해주세요
            </>
          }
        />
      }
      footer={<OnboardingBackButton onPrev={onPrev} />}
    >
      <div className="w-[220px] h-[220px] border-2 border-red-400 rounded-xl" />
    </OnboardingLayout>
  );
}

export default QRStep;