import { useEffect, useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import RoundedInput from '../components/RoundedInput.jsx';
import StaticMap from '../components/StaticMap.jsx';
import { loadKakaoMap } from '@/utils/loadKakaoMap.js';

const DUMMY_STORE_LOCATION = {
  storeName: '바나프레소 테헤란로점',
  address: '서울 강남구 테헤란로 208',
  latitude: 37.50110749596674,
  longitude: 127.03902157364993,
};

function LocationStep({ onNext, onPrev }) {
  const [storeLocation, setStoreLocation] = useState(DUMMY_STORE_LOCATION);
  const [searchKeyword, setSearchKeyword] = useState(
    DUMMY_STORE_LOCATION.storeName
  );
  const [places, setPlaces] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    const keyword = searchKeyword.trim();

    if (!keyword || keyword === storeLocation.storeName) {
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const kakao = await loadKakaoMap();
        const placesService = new kakao.maps.services.Places();

        setIsSearching(true);

        placesService.keywordSearch(keyword, (data, status) => {
          setIsSearching(false);

          if (status === kakao.maps.services.Status.OK) {
            setPlaces(data.slice(0, 5));
            return;
          }

          setPlaces([]);
        });
      } catch (error) {
        setIsSearching(false);
        setPlaces([]);
        console.error('카카오맵 검색 로드 실패:', error);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [searchKeyword, storeLocation.storeName]);

  const handleChangeKeyword = (e) => {
    const nextKeyword = e.target.value;

    setSearchKeyword(nextKeyword);

    if (!nextKeyword.trim() || nextKeyword === storeLocation.storeName) {
      setPlaces([]);
      setIsSearching(false);
    }
  };

  const handleSelectPlace = (place) => {
    const nextStoreLocation = {
      storeName: place.place_name,
      address: place.road_address_name || place.address_name,
      latitude: Number(place.y),
      longitude: Number(place.x),
    };

    setStoreLocation(nextStoreLocation);
    setSearchKeyword(place.place_name);
    setPlaces([]);
    setIsSearching(false);
  };

  const handleSave = () => {
    onNext?.();
  };

  const isNextDisabled =
    !storeLocation.storeName ||
    !storeLocation.address ||
    !storeLocation.latitude ||
    !storeLocation.longitude;

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
                가게 위치
              </span>
              를
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
          onNext={handleSave}
          nextText="저장"
          nextDisabled={isNextDisabled}
        />
      }
    >
      <div className="relative mt-2 w-full">
        <RoundedInput
          value={searchKeyword}
          onChange={handleChangeKeyword}
          placeholder="가게명을 입력해 주세요"
          icon="search"
        />

        {isSearching && (
          <p className="mt-2 text-sm text-gray-400">
            검색 중입니다
          </p>
        )}

        {places.length > 0 && (
          <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-xl border border-gray-200 bg-white shadow-lg">
            {places.map((place) => (
              <button
                key={place.id}
                type="button"
                onClick={() => handleSelectPlace(place)}
                className="w-full border-b border-gray-100 px-4 py-3 text-left last:border-b-0 hover:bg-surface-200"
              >
                <p className="text-[15px] font-bold text-gray-900">
                  {place.place_name}
                </p>
                <p className="mt-1 text-[13px] text-gray-500">
                  {place.road_address_name || place.address_name}
                </p>
              </button>
            ))}
          </div>
        )}
      </div>

      <StaticMap storeLocation={storeLocation} />
    </OnboardingLayout>
  );
}

export default LocationStep;
