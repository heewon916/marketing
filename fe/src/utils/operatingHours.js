// src/utils/operatingHours.js

export const convertApiCloseTimeToDisplayTime = (closeTime) => {
  if (!closeTime) return '18:00';

  const [hour, minute] = closeTime.split(':').map(Number);

  if (hour < 24) {
    return closeTime;
  }

  return `${String(hour - 24).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
};

export const convertDisplayCloseTimeToApiTime = (startTime, endTime) => {
  if (!startTime || !endTime) return endTime;

  const [startHour, startMinute] = startTime.split(':').map(Number);
  const [endHour, endMinute] = endTime.split(':').map(Number);

  const startTotalMinutes = startHour * 60 + startMinute;
  const endTotalMinutes = endHour * 60 + endMinute;

  if (endTotalMinutes > startTotalMinutes) {
    return endTime;
  }

  return `${String(endHour + 24).padStart(2, '0')}:${String(endMinute).padStart(2, '0')}`;
};
