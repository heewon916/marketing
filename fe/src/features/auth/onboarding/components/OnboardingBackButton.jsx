import Button from '@/components/common/Button.jsx';

function OnboardingBackButton({ onPrev }) {
  return (
    <Button
      size="sm"
      variant="white"
      onClick={onPrev}
      className="w-full"
    >
      이전
    </Button>
  );
}

export default OnboardingBackButton;