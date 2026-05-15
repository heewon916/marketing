import { useEffect, useRef, useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import RoundedInput from '../components/RoundedInput.jsx';
import StaticMap from '../components/StaticMap.jsx';
import { loadKakaoMap } from '@/utils/loadKakaoMap.js';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

function LocationStep({ onNext, onPrev }) {
  const storeName = useOnboardingStore((state) => state.storeName);
  const savedAddress = useOnboardingStore((state) => state.address);
  const savedLatitude = useOnboardingStore((state) => state.latitude);
  const savedLongitude = useOnboardingStore((state) => state.longitude);

  const setLocation = useOnboardingStore((state) => state.setLocation);

  const [storeLocation, setStoreLocation] = useState(() => ({
    placeName: storeName || '',
    address: savedAddress || '',
    latitude: savedLatitude,
    longitude: savedLongitude,
  }));

  const [searchKeyword, setSearchKeyword] = useState(() => storeName || '');
  const [inputValue, setInputValue] = useState(() => storeName || '');
  const [places, setPlaces] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');

  const latestSearchKeywordRef = useRef('');

  useEffect(() => {
    const keyword = searchKeyword.trim();

    latestSearchKeywordRef.current = keyword;

    if (!keyword) {
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const kakao = await loadKakaoMap();
        const placesService = new kakao.maps.services.Places();

        placesService.keywordSearch(keyword, (data, status) => {
          if (latestSearchKeywordRef.current !== keyword) {
            return;
          }

          if (status === kakao.maps.services.Status.OK) {
            const nextPlaces = data.slice(0, 5);

            setPlaces(nextPlaces);
            setErrorMessage('');

            if (nextPlaces.length === 1) {
              const firstPlace = nextPlaces[0];

              setStoreLocation({
                placeName: firstPlace.place_name,
                address: firstPlace.road_address_name || firstPlace.address_name,
                latitude: Number(firstPlace.y),
                longitude: Number(firstPlace.x),
              });

              setPlaces([]);
            }

            return;
          }

          setPlaces([]);
          setErrorMessage('검색 결과를 찾을 수 없습니다. 가게명을 다시 입력해 주세요.');
        });
      } catch {
        if (latestSearchKeywordRef.current !== keyword) {
          return;
        }

        setPlaces([]);
        setErrorMessage('지도를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.');
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [searchKeyword]);

  const handleChangeKeyword = (e) => {
    const nextKeyword = e.target.value;

    setInputValue(nextKeyword);
    setSearchKeyword(nextKeyword);
    setStoreLocation({
      placeName: nextKeyword,
      address: '',
      latitude: null,
      longitude: null,
    });

    if (!nextKeyword.trim()) {
      setPlaces([]);
      setErrorMessage('');
    }
  };

  const handleSelectPlace = (place) => {
    const nextStoreLocation = {
      placeName: place.place_name,
      address: place.road_address_name || place.address_name,
      latitude: Number(place.y),
      longitude: Number(place.x),
    };

    setStoreLocation(nextStoreLocation);
    setInputValue(place.place_name);
    setPlaces([]);
    setErrorMessage('');
  };

  const handleSave = () => {
    if (
      !storeLocation.address ||
      storeLocation.latitude == null ||
      storeLocation.longitude == null
    ) {
      return;
    }

    setLocation({
      address: storeLocation.address,
      latitude: storeLocation.latitude,
      longitude: storeLocation.longitude,
    });

    onNext?.();
  };

  const isNextDisabled =
    !storeLocation.address ||
    storeLocation.latitude == null ||
    storeLocation.longitude == null;

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
          value={inputValue}
          onChange={handleChangeKeyword}
          placeholder="가게명을 입력해 주세요"
          icon="search"
        />

        {errorMessage && (
          <p className="mt-2 text-sm font-medium text-red-500">
            {errorMessage}
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
