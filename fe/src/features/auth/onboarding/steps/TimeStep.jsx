import { useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import DayTimeRow from '../components/DayTimeRow.jsx';
import ScrollFadeArrow from '../components/ScrollFadeArrow.jsx';

const days = ['월', '화', '수', '목', '금', '토', '일'];

function TimeStep({ onNext, onPrev }) {
  const [timeData, setTimeData] = useState(
    days.map((day) => ({
      day,
      isOpen: true,
      startTime: '09:00',
      endTime: '18:00',
    }))
  );

  const updateDay = (index, key, value) => {
    setTimeData((prev) => {
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        [key]: value,
      };
      return updated;
    });
  };

  return (
    <>
      <OnboardingLayout
        currentStep={6}
        totalStep={7}
        contentAlign="left"
        header={
          <OnboardingHeader
            title={
              <>
                <span className="text-primary-100 font-extrabold">영업시간</span>을
                <br />
                확인해주세요
              </>
            }
            subtitle="정보가 다르면 수정해 주세요"
          />
        }
        footer={
          <OnboardingFooterButtons
            onPrev={onPrev}
            onNext={onNext}
            nextLabel="저장"
          />
        }
      >
        {/* 안내 카드 */}
        <div className="mt-2 w-full p-5 bg-gray-50 rounded-2xl border border-gray-100 flex flex-col gap-2">
          <div className="text-xl font-bold text-gray-900 flex items-center gap-1.5">
            <span className="material-icons text-primary-100 text-xl">info</span>
            새벽까지 영업하시나요?
          </div>

          <div className="text-[17px] text-gray-600 leading-relaxed">
            밤 12시가 넘어도 <span className="font-extrabold text-gray-900">그대로 입력</span>하세요.
          </div>

          <div className="mt-1 text-base font-medium text-gray-400">
            예: 20:00 ~ 02:00
          </div>
        </div>

        {/* 요일/시간 리스트 */}
        <div className="mt-6 w-full flex flex-col gap-3 pb-8">
          {timeData.map((item, idx) => (
            <DayTimeRow
              key={item.day}
              day={item.day}
              isOpen={item.isOpen}
              startTime={item.startTime}
              endTime={item.endTime}
              onToggle={() => updateDay(idx, 'isOpen', !item.isOpen)}
              onStartTimeChange={(val) => updateDay(idx, 'startTime', val)}
              onEndTimeChange={(val) => updateDay(idx, 'endTime', val)}
            />
          ))}
        </div>
      </OnboardingLayout>

      <ScrollFadeArrow />
    </>
  );
}

export default TimeStep;
