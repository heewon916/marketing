import Button from '@/components/common/Button.jsx';

function OnboardingFooterButtons({
  onPrev,
  onNext,
  nextText = '다음',
  prevText = '이전',
  hidePrev = false,
}) {
  return (
    <div className="flex gap-3">
      {!hidePrev && (
        <Button
          size="sm"
          variant="white"
          onClick={onPrev}
          className="flex-1"
        >
          {prevText}
        </Button>
      )}

      <Button
        size="sm"
        variant="primary"
        onClick={onNext}
        className="flex-1"
      >
        {nextText}
      </Button>
    </div>
  );
}

export default OnboardingFooterButtons;