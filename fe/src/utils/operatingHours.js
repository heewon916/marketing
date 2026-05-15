// src/utils/operatingHours.js

const koreanDayKeyMap = {
  월: 'monday',
  화: 'tuesday',
  수: 'wednesday',
  목: 'thursday',
  금: 'friday',
  토: 'saturday',
  일: 'sunday',
};

const crawlerDayKeyMap = {
  mon_hours: 'monday',
  tues_hours: 'tuesday',
  wed_hours: 'wednesday',
  thur_hours: 'thursday',
  fri_hours: 'friday',
  sat_hours: 'saturday',
  sun_hours: 'sunday',
};

export const parseOperatingHour = (value) => {
  if (typeof value !== 'string') {
    return null;
  }

  const normalizedValue = value.trim();

  if (!normalizedValue || normalizedValue === '정보없음') {
    return null;
  }

  if (normalizedValue.includes('휴무')) {
    return {
      isOpen: false,
      open: null,
      close: null,
    };
  }

  if (
    normalizedValue.includes('24시간') ||
    normalizedValue === '00:00 - 24:00'
  ) {
    return {
      isOpen: true,
      open: '00:00',
      close: '24:00',
    };
  }

  const timeMatch = normalizedValue.match(
    /(\d{2}:\d{2})\s*[-~]\s*(\d{2}:\d{2})/
  );

  if (!timeMatch) {
    return null;
  }

  const [, open, close] = timeMatch;

  return {
    isOpen: true,
    open,
    close,
  };
};

const getOperatingHoursKeyMap = (operatingHours) => {
  if (!operatingHours || typeof operatingHours !== 'object') {
    return {};
  }

  const keys = Object.keys(operatingHours);

  const hasCrawlerKeys = keys.some((key) => key.endsWith('_hours'));

  if (hasCrawlerKeys) {
    return crawlerDayKeyMap;
  }

  return koreanDayKeyMap;
};

export const convertOperatingHours = (operatingHours) => {
  if (!operatingHours || typeof operatingHours !== 'object') {
    return {};
  }

  const keyMap = getOperatingHoursKeyMap(operatingHours);

  return Object.entries(keyMap).reduce((acc, [apiKey, storeKey]) => {
    const parsedHours = parseOperatingHour(operatingHours[apiKey]);

    if (parsedHours) {
      acc[storeKey] = parsedHours;
    }

    return acc;
  }, {});
};

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
