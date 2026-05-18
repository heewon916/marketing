import { useEffect, useState } from 'react';
import Button from '@/components/common/Button';
import RoundedInput from '@/features/auth/onboarding/components/RoundedInput';
import StaticMap from '@/features/auth/onboarding/components/StaticMap';
import { loadKakaoMap } from '@/utils/loadKakaoMap';
import { accountInfoCardStyles } from './accountInfoCardStyles';
import CardShell from './CardShell';

const categories = ['식당', '주점', '카페', '제과점'];

export default function AccountInfoEdit({
  formData,
  onChange,
  onCancel,
  onSave,
}) {
  const [searchKeyword, setSearchKeyword] = useState(formData.address ?? '');

const storeLocation = {
  storeName: formData.businessName ?? '',
  address: formData.address ?? '',
  latitude: formData.latitude ?? null,
  longitude: formData.longitude ?? null,
};

  const [places, setPlaces] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  const updateField = (key, value) => {
    onChange({ ...formData, [key]: value });
  };

  useEffect(() => {
    const keyword = searchKeyword.trim();

    if (!keyword || keyword === storeLocation.address) return;

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
  }, [searchKeyword, storeLocation.address]);

  const handleChangeKeyword = (event) => {
    const nextKeyword = event.target.value;

    setSearchKeyword(nextKeyword);

    if (!nextKeyword.trim() || nextKeyword === storeLocation.address) {
      setPlaces([]);
      setIsSearching(false);
    }
  };

  const handleSelectPlace = (place) => {
    const nextStoreLocation = {
      storeName: formData.businessName,
      address: place.road_address_name || place.address_name,
      latitude: Number(place.y),
      longitude: Number(place.x),
    };

    setSearchKeyword(nextStoreLocation.address);
    setPlaces([]);
    setIsSearching(false);

    onChange({
      ...formData,
      address: nextStoreLocation.address,
      latitude: nextStoreLocation.latitude,
      longitude: nextStoreLocation.longitude,
    });
  };

  return (
    <CardShell className="flex flex-col px-7 py-8">
      <div className="flex flex-col">
        {/* 상호명 */}
        <div className={`${accountInfoCardStyles.section} flex flex-col gap-2`}>
          <span className={accountInfoCardStyles.label}>상호명</span>

          <div className="flex h-12 items-center rounded-xl border border-gray-100 bg-gray-50 px-4">
            <span className="text-[18px] font-semibold text-gray-500">
              {formData.businessName || '상호명 없음'}
            </span>
          </div>

          <p className="text-[13px] font-medium text-gray-400">
            상호명은 온보딩 이후 수정할 수 없습니다.
          </p>
        </div>

        {/* 업종 */}
        <div className={`${accountInfoCardStyles.section} flex flex-col gap-3`}>
          <span className={accountInfoCardStyles.label}>업종</span>

          <div className="grid grid-cols-2 gap-3">
            {categories.map((category) => {
              const isSelected = formData.category === category;

              return (
                <Button
                  key={category}
                  size="sm"
                  variant={isSelected ? 'primary' : 'white'}
                  onClick={() => updateField('category', category)}
                  className="w-full text-[18px] font-semibold"
                >
                  {category}
                </Button>
              );
            })}
          </div>
        </div>

        {/* 위치 */}
        <div className={`${accountInfoCardStyles.section} flex flex-col gap-3`}>
          <span className={accountInfoCardStyles.label}>위치</span>

          <div className="relative">
            <RoundedInput
              value={searchKeyword}
              onChange={handleChangeKeyword}
              placeholder="가게명 또는 주소를 입력해주세요"
              icon="search"
              className="h-12 py-0 text-[18px] font-semibold text-accent-100 placeholder:font-medium placeholder:text-gray-400"
            />

            {isSearching && (
              <p className="mt-2 text-[14px] font-medium text-gray-400">
                검색 중입니다
              </p>
            )}

            {places.length > 0 && (
              <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-xl border border-gray-200 bg-white shadow-lg">
                {places.map((place) => (
                  <Button
                    key={place.id}
                    size="lg"
                    variant="white"
                    onClick={() => handleSelectPlace(place)}
                    className="h-auto w-full rounded-none border-0 border-b border-gray-100 px-4 py-3 text-left last:border-b-0"
                  >
                    <div className="flex w-full flex-col items-start">
                      <span className="text-[15px] font-bold text-accent-100">
                        {place.place_name}
                      </span>
                      <span className="mt-1 text-[13px] font-medium text-gray-500">
                        {place.road_address_name || place.address_name}
                      </span>
                    </div>
                  </Button>
                ))}
              </div>
            )}
          </div>

          <StaticMap storeLocation={storeLocation} />
        </div>
      </div>

      {/* 하단 버튼 */}
      <div className="mt-6 flex justify-center gap-3">
        <Button
          size="sm"
          variant="white"
          onClick={onCancel}
          className="text-[18px] font-bold"
        >
          취소
        </Button>

        <Button
          size="sm"
          variant="primary"
          onClick={onSave}
          className="text-[18px] font-bold"
        >
          저장하기
        </Button>
      </div>
    </CardShell>
  );
}
