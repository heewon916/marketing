import { useEffect, useRef } from 'react';
import { renderToString } from 'react-dom/server';
import { RiMapPinFill } from "react-icons/ri";
import { loadKakaoMap } from '@/utils/loadKakaoMap.js';

const DEFAULT_POSITION = {
  latitude: 37.566826,
  longitude: 126.9786567,
};

export default function StaticMap({ storeLocation }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);

  const latitude = storeLocation?.latitude ?? DEFAULT_POSITION.latitude;
  const longitude = storeLocation?.longitude ?? DEFAULT_POSITION.longitude;

  useEffect(() => {
    const renderMap = async () => {
      try {
        if (!mapRef.current) return;

        const kakao = await loadKakaoMap();
        const position = new kakao.maps.LatLng(latitude, longitude);

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
            position: position,
            content: iconHtml,
            yAnchor: 1,
            map: map,
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
        markerRef.current.setPosition(position);
      } catch (error) {
        console.error('카카오맵 렌더링 실패:', error);
      }
    };

    renderMap();
  }, [latitude, longitude]);

  return (
    <div className="relative mt-3 h-[340px] w-full shrink-0 overflow-hidden rounded-[24px] border border-gray-200/80 bg-surface-100 shadow-sm">
      {/* 지도 영역 */}
      <div ref={mapRef} className="h-full w-full" />

      {/* 플로팅 정보 카드 */}
      <div className="pointer-events-none absolute inset-x-4 bottom-4 z-10 flex items-center gap-3 rounded-2xl bg-white/90 px-4 py-3.5 shadow-md backdrop-blur-lg border border-white/30">

        {/* 포인트 아이콘 */}
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-100 text-primary-100">
          <RiMapPinFill className="h-[24px] w-[24px]" />
        </div>

        {/* 텍스트 정보 */}
        <div className="flex flex-col">
          <p className="text-[15px] font-bold text-accent-100 leading-tight">
            {storeLocation?.placeName || '가게 위치'}
          </p>
          <p className="mt-1 text-[13px] font-medium text-gray-500 leading-tight">
            {storeLocation?.address || '주소 정보가 없습니다'}
          </p>
        </div>
      </div>
    </div>
  );
}
