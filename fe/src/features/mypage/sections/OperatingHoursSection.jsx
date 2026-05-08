import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomTab from '@/components/common/BottomTab';
import MyPageHeader from '../components/MyPageHeader';
import OperatingHoursEdit from '../components/OperatingHoursEdit';
import Button from '@/components/common/Button';

const initialOperatingHours = [
  { day: '월요일', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '화요일', isOpen: false, startTime: '11:00', endTime: '20:30' },
  { day: '수요일', isOpen: false, startTime: '11:00', endTime: '20:30' },
  { day: '목요일', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '금요일', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '토요일', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '일요일', isOpen: true, startTime: '11:00', endTime: '20:30' },
];

export default function OperatingHoursSection({ isEmbedded = false }) {
  const navigate = useNavigate();

  const [isEditing, setIsEditing] = useState(false);
  const [operatingHours, setOperatingHours] = useState(initialOperatingHours);

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

  const handleBack = () => {
    navigate('/mypage');
  };

  const content = (
    <>
      <section className="rounded-2xl bg-white px-6 py-8">
        <h2 className="text-[17px] font-bold text-gray-500">영업시간</h2>

        {isEditing ? (
          <div className="mt-6">
            <OperatingHoursEdit
              hours={operatingHours}
              onChange={setOperatingHours}
            />
          </div>
        ) : (
          <div className="mt-6 flex flex-col gap-5">
            {operatingHours.map((item) => (
              <div
                key={item.day}
                className="grid grid-cols-[80px_1fr] items-center text-[18px]"
              >
                <span className="font-bold text-accent-100">{item.day}</span>

                <span className="text-right font-medium text-accent-100">
                  {item.isOpen
                    ? `${item.startTime}  -  ${item.endTime}`
                    : '휴무'}
                </span>
              </div>
            ))}
          </div>
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
            className="w-full text-[18px] font-bold"
          >
            수정하기
          </Button>
        </div>
      )}
    </>
  );

  if (isEmbedded) {
    return <section className="flex flex-col gap-4">{content}</section>;
  }

  return (
    <div className="min-h-screen bg-[#f4f4f6] pb-28">
      <MyPageHeader title="계정 정보" showBackButton onBack={handleBack} />

      <main className="mx-auto flex w-full max-w-[430px] flex-col gap-4 px-5 pt-5">
        {content}
      </main>

      <BottomTab />
    </div>
  );
}
