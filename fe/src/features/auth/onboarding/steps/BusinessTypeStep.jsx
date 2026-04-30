import { useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import CategoryChip from '../components/CategoryChip.jsx';
import ModalCategoryGuide from '../components/ModalCategoryGuide.jsx';

const types = ['식당', '주점', '카페', '제과점'];

function BusinessTypeStep({ value, onChange, onNext, onPrev }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <OnboardingLayout
      currentStep={6}
      totalStep={7}
      contentAlign="left"
      header={
        <OnboardingHeader
          title={
            <>
              <span className="text-primary-100 font-extrabold">
                업종
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
          onPrev={onPrev}
          onNext={onNext}
          nextText="저장"
          nextDisabled={!value}
        />
      }
    >
      <>
        {/* 업종 선택 */}
        <div className="grid grid-cols-2 gap-3 mt-2 w-full">
          {types.map((type) => (
            <CategoryChip
              key={type}
              label={type}
              isSelected={value === type}
              onClick={() => onChange(type)}
            />
          ))}

          {/* 가운데 정렬 */}
          <div className="col-span-2 flex justify-center">
            <button
              onClick={() => setIsModalOpen(true)}
              className="mt-6 text-base text-gray-500 underline underline-offset-4"
            >
              업종 설명이 필요하신가요?
            </button>
          </div>
        </div>

        {/* 모달 */}
        <ModalCategoryGuide
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
        />
      </>
    </OnboardingLayout>
  );
}

export default BusinessTypeStep;
