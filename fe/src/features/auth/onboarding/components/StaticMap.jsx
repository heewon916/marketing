import { useEffect, useRef } from 'react';
import { renderToString } from 'react-dom/server';
import { RiMapPinFill } from 'react-icons/ri';
import { loadKakaoMap } from '@/utils/loadKakaoMap.js';

const DEFAULT_POSITION = {
  latitude: 37.566826,
  longitude: 126.9786567,
};

const isValidCoordinate = (latitude, longitude) => {
  if (
    latitude === null ||
    latitude === undefined ||
    latitude === '' ||
    longitude === null ||
    longitude === undefined ||
    longitude === ''
  ) {
    return false;
  }

  const lat = Number(latitude);
  const lng = Number(longitude);

  return !Number.isNaN(lat) && !Number.isNaN(lng);
};

const getPositionByAddress = (kakao, address) =>
  new Promise((resolve) => {
    if (!address?.trim()) {
      resolve(null);
      return;
    }

    const geocoder = new kakao.maps.services.Geocoder();

    geocoder.addressSearch(address, (result, status) => {
      if (status !== kakao.maps.services.Status.OK || result.length === 0) {
        resolve(null);
        return;
      }

      const { y, x } = result[0];

      resolve({
        latitude: Number(y),
        longitude: Number(x),
      });
    });
  });

export default function StaticMap({ storeLocation }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);

  const latitude = storeLocation?.latitude;
  const longitude = storeLocation?.longitude;
  const address = storeLocation?.address;

  useEffect(() => {
    const renderMap = async () => {
      try {
        if (!mapRef.current) return;

        const kakao = await loadKakaoMap();

        let nextPosition = null;

        if (isValidCoordinate(latitude, longitude)) {
          nextPosition = {
            latitude: Number(latitude),
            longitude: Number(longitude),
          };
        } else {
          nextPosition = await getPositionByAddress(kakao, address);
        }

        const position = new kakao.maps.LatLng(
          nextPosition?.latitude ?? DEFAULT_POSITION.latitude,
          nextPosition?.longitude ?? DEFAULT_POSITION.longitude
        );

        if (!mapInstanceRef.current) {
          const map = new kakao.maps.Map(mapRef.current, {
            center: position,
            level: 3,
            draggable: true,
            scrollwheel: true,
          });

          // 1. 순수 아이콘만 렌더링
          const iconHtml = renderToString(
            <div className="text-primary-100">
              <RiMapPinFill style={{ width: '50px', height: '50px' }} />
            </div>
          );

          // 2. CustomOverlay 생성
          const customOverlay = new kakao.maps.CustomOverlay({
            position,
            content: iconHtml,
            yAnchor: 1,
            map,
          });

          mapInstanceRef.current = map;
          markerRef.current = customOverlay;

          setTimeout(() => {
            map.relayout();
            map.setCenter(position);
          }, 0);

          return;
        }

        mapInstanceRef.current.setCenter(position);
        markerRef.current?.setPosition(position);
      } catch (error) {
        console.error('카카오맵 렌더링 실패:', error);
      }
    };

    renderMap();
  }, [latitude, longitude, address]);

  return (
    <div className="relative mt-3 h-[340px] w-full shrink-0 overflow-hidden rounded-[24px] border border-gray-200/80 bg-surface-100 shadow-sm">
      {/* 지도 영역 */}
      <div ref={mapRef} className="h-full w-full" />

      {/* 플로팅 정보 카드 */}
      <div className="pointer-events-none absolute inset-x-4 bottom-4 z-10 flex items-center gap-3 rounded-2xl border border-white/30 bg-white/90 px-4 py-3.5 shadow-md backdrop-blur-lg">

        {/* 포인트 아이콘 */}
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-100 text-primary-100">
          <RiMapPinFill className="h-[24px] w-[24px]" />
        </div>

        {/* 텍스트 정보 */}
        <div className="flex flex-col">
          <p className="text-[15px] font-bold leading-tight text-accent-100">
            {storeLocation?.storeName || storeLocation?.placeName || '가게 위치'}
          </p>
          <p className="mt-1 text-[13px] font-medium leading-tight text-gray-500">
            {storeLocation?.address || '주소 정보가 없습니다'}
          </p>
        </div>
      </div>
    </div>
  );
}
