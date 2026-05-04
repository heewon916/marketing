import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomTab from '@/components/common/BottomTab';
import AccountHeader from '../components/AccountHeader';
import AccountProfile from '../components/AccountProfile';
import AccountTabSwitcher from '../components/AccountTabSwitcher';
import OperatingHoursList from '../components/OperatingHoursList';
import OperatingHoursEdit from '../components/OperatingHoursEdit';

const accountMockData = {
  storeName: '싸피 카페',
  instagramUsername: '@ssafy_cafe',
};

const initialOperatingHours = [
  {
    day: '월',
    isOpen: true,
    startTime: '11:00',
    endTime: '20:30',
  },
  {
    day: '화',
    isOpen: false,
    startTime: '11:00',
    endTime: '20:30',
  },
  {
    day: '수',
    isOpen: false,
    startTime: '11:00',
    endTime: '20:30',
  },
  {
    day: '목',
    isOpen: true,
    startTime: '11:00',
    endTime: '20:30',
  },
  {
    day: '금',
    isOpen: true,
    startTime: '11:00',
    endTime: '20:30',
  },
  {
    day: '토',
    isOpen: true,
    startTime: '11:00',
    endTime: '20:30',
  },
  {
    day: '일',
    isOpen: true,
    startTime: '11:00',
    endTime: '20:30',
  },
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
    <div className="min-h-screen bg-white pb-24">
      <main className="mx-auto flex min-h-screen w-full max-w-[430px] flex-col px-6 pt-6">
        <AccountHeader title="계정 정보" />

        <div className="mt-11">
          <AccountProfile
            storeName={accountMockData.storeName}
            instagramUsername={accountMockData.instagramUsername}
          />
        </div>

        <div className="mt-11 px-4">
          <AccountTabSwitcher
            activeTab="hours"
            onChange={handleTabChange}
          />
        </div>

        <section className="mt-16">
          <h2 className="text-[18px] font-bold text-gray-500">
            영업 시간
          </h2>

          <div className="mt-6">
            {isEditing ? (
              <OperatingHoursEdit
                hours={operatingHours}
                onChange={setOperatingHours}
              />
            ) : (
              <OperatingHoursList hours={operatingHours} />
            )}
          </div>
        </section>

        {isEditing ? (
          <div className="mt-auto mb-5 grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={handleCancelClick}
              className="h-14 w-full rounded-xl border border-gray-200 bg-white text-[20px] font-extrabold text-gray-500"
            >
              취소
            </button>

            <button
              type="button"
              onClick={handleSaveClick}
              className="h-14 w-full rounded-xl bg-primary-100 text-[20px] font-extrabold text-white"
            >
              저장하기
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={handleEditClick}
            className="mt-auto mb-5 h-14 w-full rounded-xl bg-primary-100 text-[20px] font-extrabold text-white"
          >
            수정하기
          </button>
        )}
      </main>

      <BottomTab />
    </div>
  );
}
