import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomTab from '@/components/common/BottomTab';
import AccountHeader from '../components/AccountHeader';
import AccountProfile from '../components/AccountProfile';
import AccountTabSwitcher from '../components/AccountTabSwitcher';
import OperatingHoursList from '../components/OperatingHoursList';
import OperatingHoursEdit from '../components/OperatingHoursEdit';
import Button from '@/components/common/Button';

const accountMockData = {
  storeName: '싸피 카페',
  instagramUsername: '@ssafy_cafe',
};

const initialOperatingHours = [
  { day: '월', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '화', isOpen: false, startTime: '11:00', endTime: '20:30' },
  { day: '수', isOpen: false, startTime: '11:00', endTime: '20:30' },
  { day: '목', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '금', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '토', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '일', isOpen: true, startTime: '11:00', endTime: '20:30' },
];

export default function OperatingHoursSection({ onTabChange }) {
  const navigate = useNavigate();

  const [isEditing, setIsEditing] = useState(false);
  const [operatingHours, setOperatingHours] = useState(initialOperatingHours);

  const handleTabChange = (tab) => {
    if (isEditing) return;

    if (tab === 'info') {
      if (onTabChange) {
        onTabChange(tab);
        return;
      }

      navigate('/mypage/account');
    }
  };

  const handleEditClick = () => {
    setIsEditing(true);
  };

  const handleCancelClick = () => {
    setOperatingHours(initialOperatingHours);
    setIsEditing(false);
  };

  const handleSaveClick = () => {
    // TODO: 영업시간 수정 API 연결
    setIsEditing(false);
  };

  return (
    <div className="min-h-screen bg-accent-100/5 pb-28">
      <AccountHeader
        title='계정 정보'
        hideBackButton={isEditing}
      />

      <main className="mx-auto flex w-full max-w-[430px] flex-col gap-4 px-5 pt-4">
        <AccountProfile
          storeName={accountMockData.storeName}
          instagramUsername={accountMockData.instagramUsername}
        />

        <AccountTabSwitcher
          activeTab="hours"
          onChange={handleTabChange}
        />

        <section className="flex flex-col gap-3">
          <h2 className="px-1 text-[16px] font-bold text-gray-500">
            영업 시간
          </h2>

          {isEditing ? (
            <OperatingHoursEdit
              hours={operatingHours}
              onChange={setOperatingHours}
            />
          ) : (
            <OperatingHoursList hours={operatingHours} />
          )}
        </section>

        {isEditing ? (
          <div className="mt-2 flex justify-center gap-3">
            <Button
              size="sm"
              variant="white"
              onClick={handleCancelClick}
              className="text-[18px] font-bold"
            >
              취소
            </Button>

            <Button
              size="sm"
              variant="primary"
              onClick={handleSaveClick}
              className="text-[18px] font-bold"
            >
              저장하기
            </Button>
          </div>
        ) : (
          <div className="mt-2 flex justify-center">
            <Button
              size="lg"
              variant="primary"
              onClick={handleEditClick}
              className="text-[18px] font-bold"
            >
              수정하기
            </Button>
          </div>
        )}
      </main>

      <BottomTab />
    </div>
  );
}
