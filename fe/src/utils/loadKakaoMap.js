const KAKAO_MAP_SCRIPT_ID = 'kakao-map-script';

export function loadKakaoMap() {
  return new Promise((resolve, reject) => {
    const kakaoMapKey = import.meta.env.VITE_KAKAO_MAP_KEY;

    if (!kakaoMapKey) {
      reject(new Error('VITE_KAKAO_MAP_KEY가 설정되지 않았습니다.'));
      return;
    }

    if (window.kakao?.maps) {
      window.kakao.maps.load(() => resolve(window.kakao));
      return;
    }

    const existingScript = document.getElementById(KAKAO_MAP_SCRIPT_ID);

    if (existingScript) {
      existingScript.addEventListener('load', () => {
        window.kakao.maps.load(() => resolve(window.kakao));
      });

      existingScript.addEventListener('error', () => {
        reject(
          new Error(
            '카카오맵 SDK 스크립트 로드에 실패했습니다. JavaScript 키와 등록 도메인을 확인해 주세요.'
          )
        );
      });

      return;
    }

    const script = document.createElement('script');

    script.id = KAKAO_MAP_SCRIPT_ID;
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${kakaoMapKey}&libraries=services&autoload=false`;
    script.async = true;

    script.onload = () => {
      window.kakao.maps.load(() => resolve(window.kakao));
    };

    script.onerror = () => {
      script.remove();

      reject(
        new Error(
          '카카오맵 SDK 스크립트 로드에 실패했습니다. JavaScript 키와 등록 도메인을 확인해 주세요.'
        )
      );
    };

    document.head.appendChild(script);
  });
}
