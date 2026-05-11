import { useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import CategoryChip from '../components/CategoryChip.jsx';
import ModalCategoryGuide from '../components/ModalCategoryGuide.jsx';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

const types = ['식당', '주점', '카페', '제과점'];

function BusinessTypeStep({ value = '', onChange, onNext, onPrev }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const category = useOnboardingStore((state) => state.category);
  const suggestedCategory = useOnboardingStore(
    (state) => state.suggestedCategory
  );
  const setCategory = useOnboardingStore((state) => state.setCategory);

  const [selectedCategory, setSelectedCategory] = useState(
    () => category || value || suggestedCategory || ''
  );

  const handleSelectCategory = (type) => {
    setSelectedCategory(type);
    onChange?.(type);
  };

  const handleNext = () => {
    if (!selectedCategory) return;

    setCategory(selectedCategory);
    onChange?.(selectedCategory);
    onNext?.();
  };

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
          onNext={handleNext}
          nextText="저장"
          nextDisabled={!selectedCategory}
        />
      }
    >
      <>
        <div className="grid grid-cols-2 gap-3 mt-2 w-full">
          {types.map((type) => (
            <CategoryChip
              key={type}
              label={type}
              isSelected={selectedCategory === type}
              onClick={() => handleSelectCategory(type)}
            />
          ))}

          <div className="col-span-2 flex justify-center">
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="mt-6 text-base text-gray-500 underline underline-offset-4"
            >
              업종 설명이 필요하신가요?
            </button>
          </div>
        </div>

        <ModalCategoryGuide
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
        />
      </>
    </OnboardingLayout>
  );
}

export default BusinessTypeStep;
