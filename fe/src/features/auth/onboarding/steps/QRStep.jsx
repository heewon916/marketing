import { useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import BackButton from '../components/BackButton.jsx';
import QRScanner from '../components/QRScanner.jsx';
import { onboardingApi } from '@/features/auth/onboarding/api.js';

function QRStep({ onPrev, onSuccess, onVerified }) {
  const [isVerifying, setIsVerifying] = useState(false);
  const [isScanCompleted, setIsScanCompleted] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const extractPinFromQrValue = (qrValue) => {
    if (!qrValue) return '';

    try {
      const parsedUrl = new URL(qrValue);
      const pin = parsedUrl.searchParams.get('pin');

      if (pin) {
        return pin.replace(/[^0-9]/g, '').slice(0, 6);
      }
    } catch {
      // QR 값이 URL이 아닌 경우 아래 숫자 추출 로직으로 처리
    }

    return qrValue.replace(/[^0-9]/g, '').slice(0, 6);
  };

  const handleScanSuccess = async (qrValue) => {
    if (isVerifying || isScanCompleted) return;

    const pin = extractPinFromQrValue(qrValue);

    if (pin.length !== 6) {
      setErrorMessage('QR 코드에서 6자리 인증 코드를 찾을 수 없습니다.');
      return;
    }

    try {
      setIsVerifying(true);
      setIsScanCompleted(true);
      setErrorMessage('');

      const response = await onboardingApi.verifyPosPin(pin);
      const { success, merchantId, message } = response.data;

      if (!success || !merchantId) {
        setErrorMessage(message || 'QR 인증에 실패했습니다.');
        setIsScanCompleted(false);
        return;
      }

      onVerified?.(merchantId);
      onSuccess?.();
    } catch (error) {
      const message =
        error.response?.data?.message ||
        'QR 인증 중 오류가 발생했습니다. 다시 시도해 주세요.';

      setErrorMessage(message);
      setIsScanCompleted(false);
    } finally {
      setIsVerifying(false);
    }
  };

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
          subtitle={
            <>
              토스 POS 화면에 표시된 QR을
              <br />
              카메라로 인식해 주세요.
            </>
          }
        />
      }
      footer={<BackButton onPrev={onPrev} />}
    >
      <div className="flex flex-col items-center w-full">
        <QRScanner
          onSuccess={handleScanSuccess}
          disabled={isVerifying || isScanCompleted}
        />

        {isVerifying && (
          <p className="mt-4 text-sm font-medium text-gray-500">
            QR 인증을 확인하고 있어요.
          </p>
        )}

        {errorMessage && (
          <p className="mt-4 text-sm font-medium text-red-500 text-center">
            {errorMessage}
          </p>
        )}
      </div>
    </OnboardingLayout>
  );
}

export default QRStep;
