import { useEffect, useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import RoundedInput from '../components/RoundedInput.jsx';
import StaticMap from '../components/StaticMap.jsx';
import { loadKakaoMap } from '@/utils/loadKakaoMap.js';
import { onboardingApi } from '@/features/auth/onboarding/api.js';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

function LocationStep({ onNext, onPrev }) {
  const storeName = useOnboardingStore((state) => state.storeName);
  const selectedPlaceId = useOnboardingStore((state) => state.selectedPlaceId);
  const savedAddress = useOnboardingStore((state) => state.address);
  const savedLatitude = useOnboardingStore((state) => state.latitude);
  const savedLongitude = useOnboardingStore((state) => state.longitude);

  const setLocation = useOnboardingStore((state) => state.setLocation);
  const setOperatingHours = useOnboardingStore(
    (state) => state.setOperatingHours
  );

  const [storeLocation, setStoreLocation] = useState(() => ({
    placeName: storeName || '',
    address: savedAddress || '',
    latitude: savedLatitude,
    longitude: savedLongitude,
  }));

  const [searchKeyword, setSearchKeyword] = useState(() => storeName || '');
  const [inputValue, setInputValue] = useState(() => storeName || '');
  const [places, setPlaces] = useState([]);
  // const [isSearching, setIsSearching] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(
    () => !!selectedPlaceId
  );
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!selectedPlaceId) return;

    const fetchStoreDetail = async () => {
      try {
        const response = await onboardingApi.getStoreDetail(selectedPlaceId);
        const data = response.data?.data ?? response.data;

        const location = data?.location ?? data;
        const operatingHours = data?.operatingHours ?? {};

        const nextStoreLocation = {
          address: location?.address ?? '',
          latitude:
            location?.latitude !== undefined && location?.latitude !== null
              ? Number(location.latitude)
              : null,
          longitude:
            location?.longitude !== undefined && location?.longitude !== null
              ? Number(location.longitude)
              : null,
        };

        setStoreLocation((prev) => ({
          ...prev,
          placeName: prev.placeName || storeName || '',
          address: nextStoreLocation.address,
          latitude: nextStoreLocation.latitude,
          longitude: nextStoreLocation.longitude,
        }));
        setSearchKeyword(storeName || nextStoreLocation.address || '');
        setLocation({
          address: nextStoreLocation.address,
          latitude: nextStoreLocation.latitude,
          longitude: nextStoreLocation.longitude,
        });
        setOperatingHours(operatingHours);
        setErrorMessage('');
      } catch (error) {
        const message =
          error.response?.data?.message ||
          '가게 상세 정보를 불러오지 못했습니다. 직접 검색해 주세요.';

        setErrorMessage(message);
      } finally {
        setIsDetailLoading(false);
      }
    };

    void fetchStoreDetail();
  }, [
    selectedPlaceId,
    storeName,
    setLocation,
    setOperatingHours,
  ]);

  useEffect(() => {
    const keyword = searchKeyword.trim();

    if (!keyword) {
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const kakao = await loadKakaoMap();
        const placesService = new kakao.maps.services.Places();

        // setIsSearching(true);

        placesService.keywordSearch(keyword, (data, status) => {
          // setIsSearching(false);

          if (status === kakao.maps.services.Status.OK) {
            const nextPlaces = data.slice(0, 5);
            const firstPlace = nextPlaces[0];

            setPlaces(nextPlaces);

            if (firstPlace) {
              setStoreLocation({
                placeName: firstPlace.place_name,
                address: firstPlace.road_address_name || firstPlace.address_name,
                latitude: Number(firstPlace.y),
                longitude: Number(firstPlace.x),
              });
            }

            return;
          }

          setPlaces([]);
        });
      } catch (error) {
        // setIsSearching(false);
        setPlaces([]);
        console.error('카카오맵 검색 로드 실패:', error);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [searchKeyword]);

  const handleChangeKeyword = (e) => {
    const nextKeyword = e.target.value;

    setInputValue(nextKeyword);
    setSearchKeyword(nextKeyword);

    if (!nextKeyword.trim()) {
      setPlaces([]);
      // setIsSearching(false);
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
    // setIsSearching(false);
    setErrorMessage('');
  };

  const handleSave = () => {
    if (
      !storeLocation.address ||
      !storeLocation.latitude ||
      !storeLocation.longitude
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
    isDetailLoading ||
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
          value={inputValue}
          onChange={handleChangeKeyword}
          placeholder="가게명을 입력해 주세요"
          icon="search"
        />

        {/* {isDetailLoading && (
          <p className="mt-2 text-sm text-gray-400">
            가게 상세 정보를 불러오고 있어요.
          </p>
        )}

        {isSearching && (
          <p className="mt-2 text-sm text-gray-400">
            검색 중입니다.
          </p>
        )} */}

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
