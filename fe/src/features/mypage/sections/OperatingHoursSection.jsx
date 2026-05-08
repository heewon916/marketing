import { useState } from 'react';
import OperatingHoursEdit from '../components/OperatingHoursEdit';
import OperatingHoursList from '../components/OperatingHoursList';
import Button from '@/components/common/Button';

const initialOperatingHours = [
  { day: '월', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '화', isOpen: false, startTime: '11:00', endTime: '20:30' },
  { day: '수', isOpen: false, startTime: '11:00', endTime: '20:30' },
  { day: '목', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '금', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '토', isOpen: true, startTime: '11:00', endTime: '20:30' },
  { day: '일', isOpen: true, startTime: '11:00', endTime: '20:30' },
];

export default function OperatingHoursSection() {
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

  return (
    <section className="flex flex-col gap-4">
      {isEditing ? (
        <OperatingHoursEdit
          hours={operatingHours}
          onChange={setOperatingHours}
        />
      ) : (
        <OperatingHoursList hours={operatingHours} />
      )}

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
    </section>
  );
}
