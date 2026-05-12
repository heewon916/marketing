import Button from '@/components/common/Button.jsx';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingChecklist from '../components/OnboardingChecklist.jsx';

function StartStep({ onNext }) {
  return (
    <OnboardingLayout
      currentStep={1}
      totalStep={7}
      contentAlign="left"
      header={
        <OnboardingHeader
          title={
            <>
              맡케팅 시작 전,
              <br />
              <span className="text-primary-100 font-extrabold">준비물 3가지!</span>
            </>
          }
          subtitle={
            <>
              가게를{' '}
              <span className="text-primary-100 font-medium">맡케팅</span>
              이 완벽히 홍보하기 위해,
              <br />
              아래 항목들을 먼저 체크해 주세요!
            </>
          }
        />
      }
      footer={
        <Button onClick={onNext} className="w-full font-bold">
          확인했어요!
        </Button>
      }
    >
      <OnboardingChecklist
        items={[
          {
            title: '인스타그램 비즈니스 계정',
            desc: '가게의 예쁜 얼굴이에요!',
          },
          {
            title: '토스 POS',
            desc: '토스 POS를 사용하고 있어야 해요!',
          },
          {
            title: '네이버 플레이스',
            desc: <>가게를 찾는 손님들에게 꼭 필요한<br />이정표예요!</>,
          },
        ]}
      />
    </OnboardingLayout>
  );
}

export default StartStep;
