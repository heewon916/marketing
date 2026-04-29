import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import BackButton from '../components/BackButton.jsx';
import QRScanner from '../components/QRScanner.jsx';

function QRStep({ onPrev, onSuccess }) {
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
      footer={<BackButton onPrev={onPrev} />}
    >
      <QRScanner onSuccess={onSuccess} />
    </OnboardingLayout>
  );
}

export default QRStep;