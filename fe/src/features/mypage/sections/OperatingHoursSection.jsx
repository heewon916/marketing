import { useState } from 'react';
import OperatingHoursEdit from '../components/OperatingHoursEdit';
import OperatingHoursList from '../components/OperatingHoursList';
import { mypageApi } from '@/features/mypage/api';
import {
  convertApiCloseTimeToDisplayTime,
  convertDisplayCloseTimeToApiTime,
} from '@/utils/operatingHours.js';

const DAY_MAP = [
  { apiKey: 'monday', label: '월' },
  { apiKey: 'tuesday', label: '화' },
  { apiKey: 'wednesday', label: '수' },
  { apiKey: 'thursday', label: '목' },
  { apiKey: 'friday', label: '금' },
  { apiKey: 'saturday', label: '토' },
  { apiKey: 'sunday', label: '일' },
];

const DEFAULT_START_TIME = '11:00';
const DEFAULT_END_TIME = '20:30';

const createHoursFromApi = (operatingHours) => {
  return DAY_MAP.map(({ apiKey, label }) => {
    const dayHours = operatingHours?.[apiKey];

    return {
      day: label,
      apiKey,
      isOpen: Boolean(dayHours?.open && dayHours?.close),
      startTime: dayHours?.open ?? DEFAULT_START_TIME,
      endTime: dayHours?.close
        ? convertApiCloseTimeToDisplayTime(dayHours.close)
        : DEFAULT_END_TIME,
    };
  });
};

const createOperatingHoursRequestBody = (hours) => {
  return hours.reduce((acc, item) => {
    acc[item.apiKey] = item.isOpen
      ? {
          open: item.startTime,
          close: convertDisplayCloseTimeToApiTime(
            item.startTime,
            item.endTime
          ),
        }
      : {
          open: null,
          close: null,
        };

    return acc;
  }, {});
};

export default function OperatingHoursSection({ operatingHours, onRefresh }) {
  const [isEditing, setIsEditing] = useState(false);
  const [hours, setHours] = useState(() =>
    createHoursFromApi(operatingHours)
  );
  const [isSaving, setIsSaving] = useState(false);

  const displayHours = isEditing
    ? hours
    : createHoursFromApi(operatingHours);

  const handleEditClick = () => {
    setHours(createHoursFromApi(operatingHours));
    setIsEditing(true);
  };

  const handleCancelClick = () => {
    setHours(createHoursFromApi(operatingHours));
    setIsEditing(false);
  };

  const handleSaveClick = async (nextHours = hours) => {
    const requestBody = {
      operatingHours: createOperatingHoursRequestBody(nextHours),
    };

    try {
      setIsSaving(true);

      console.log('영업시간 수정 요청:', requestBody);

      await mypageApi.updateMyInfo(requestBody);

      if (onRefresh) {
        await onRefresh();
      }

      setIsEditing(false);
    } catch (error) {
      console.error('영업시간 수정 실패:', error);
      alert('영업시간을 수정하지 못했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="flex flex-col gap-4">
      {isEditing ? (
        <OperatingHoursEdit
          hours={hours}
          onChange={setHours}
          onCancel={handleCancelClick}
          onSave={handleSaveClick}
          isSaving={isSaving}
        />
      ) : (
        <OperatingHoursList
          hours={displayHours}
          onEdit={handleEditClick}
        />
      )}
    </section>
  );
}
