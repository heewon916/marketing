import { useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import DayTimeRow from '../components/DayTimeRow.jsx';
import ScrollFadeArrow from '../../../../components/common/ScrollFadeArrow.jsx';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';
import {
  convertApiCloseTimeToDisplayTime,
  convertDisplayCloseTimeToApiTime,
} from '@/utils/operatingHours.js';

const days = ['월', '화', '수', '목', '금', '토', '일'];

const dayKeyMap = {
  월: 'monday',
  화: 'tuesday',
  수: 'wednesday',
  목: 'thursday',
  금: 'friday',
  토: 'saturday',
  일: 'sunday',
};

const DEFAULT_START_TIME = '09:00';
const DEFAULT_END_TIME = '18:00';

const isValidOpenTime = (value) =>
  typeof value === 'string' && /^([01]\d|2[0-3]):[0-5]\d$/.test(value);

const isValidCloseTime = (value) =>
  typeof value === 'string' && /^(?:[01]\d|2\d|3\d|4[0-7]):[0-5]\d$/.test(value);

const createDefaultTimeData = () =>
  days.map((day) => ({
    day,
    isOpen: false,
    startTime: DEFAULT_START_TIME,
    endTime: DEFAULT_END_TIME,
  }));

const convertOperatingHoursToTimeData = (operatingHours) => {
  if (!operatingHours || Object.keys(operatingHours).length === 0) {
    return createDefaultTimeData();
  }

  return days.map((day) => {
    const dayKey = dayKeyMap[day];
    const savedTime = operatingHours[dayKey];

    if (!savedTime) {
      return {
        day,
        isOpen: false,
        startTime: DEFAULT_START_TIME,
        endTime: DEFAULT_END_TIME,
      };
    }

    if (savedTime.isOpen === false) {
      return {
        day,
        isOpen: false,
        startTime: isValidOpenTime(savedTime.open)
          ? savedTime.open
          : DEFAULT_START_TIME,
        endTime: isValidCloseTime(savedTime.close)
          ? convertApiCloseTimeToDisplayTime(savedTime.close)
          : DEFAULT_END_TIME,
      };
    }

    const hasValidTimeRange =
      isValidOpenTime(savedTime.open) && isValidCloseTime(savedTime.close);

    if (!hasValidTimeRange) {
      return {
        day,
        isOpen: false,
        startTime: DEFAULT_START_TIME,
        endTime: DEFAULT_END_TIME,
      };
    }

    return {
      day,
      isOpen: true,
      startTime: savedTime.open,
      endTime: convertApiCloseTimeToDisplayTime(savedTime.close),
    };
  });
};

const convertTimeDataToOperatingHours = (timeData) =>
  timeData.reduce((acc, item) => {
    const dayKey = dayKeyMap[item.day];

    acc[dayKey] = {
      isOpen: item.isOpen,
      open: item.isOpen ? item.startTime : null,
      close: item.isOpen
        ? convertDisplayCloseTimeToApiTime(item.startTime, item.endTime)
        : null,
    };

    return acc;
  }, {});

function TimeStep({ onNext, onPrev, onChange }) {
  const operatingHours = useOnboardingStore((state) => state.operatingHours);
  const setOperatingHours = useOnboardingStore(
    (state) => state.setOperatingHours
  );

  const [timeData, setTimeData] = useState(() =>
    convertOperatingHoursToTimeData(operatingHours)
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

  const saveOperatingHours = () => {
    const nextOperatingHours = convertTimeDataToOperatingHours(timeData);

    setOperatingHours(nextOperatingHours);
    onChange?.(nextOperatingHours);

    return nextOperatingHours;
  };

  const handleNext = () => {
    saveOperatingHours();
    onNext?.();
  };

  const handlePrev = () => {
    saveOperatingHours();
    onPrev?.();
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
                <span className="text-primary-100 font-extrabold">
                  영업시간
                </span>
                을
                <br />
                확인해주세요
              </>
            }
            subtitle="정보가 다르면 수정해 주세요"
          />
        }
        footer={
          <OnboardingFooterButtons
            onPrev={handlePrev}
            onNext={handleNext}
            nextText="저장"
          />
        }
      >
        <div className="mt-2 w-full p-5 bg-gray-50 rounded-2xl border border-gray-100 flex flex-col gap-2">
          <div className="text-xl font-bold text-gray-900 flex items-center gap-1.5">
            <span className="material-icons text-primary-100 text-xl">
              info
            </span>
            새벽까지 영업하시나요?
          </div>

          <div className="text-[17px] text-gray-600 leading-relaxed">
            밤 12시가 넘어도{' '}
            <span className="font-extrabold text-gray-900">
              그대로 입력
            </span>
            하세요.
          </div>

          <div className="mt-1 text-base font-medium text-gray-400">
            예: 20:00 ~ 02:00
          </div>
        </div>

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
