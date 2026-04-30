# 🛠️ [맡케팅] 포스기용 프론트엔드(플러그인) 개발 가이드

안녕하세요! 맡케팅 프로젝트에 오신 것을 환영합니다. 
이 문서는 사장님들 매장에 있는 **'토스 포스기(POS) 화면' 안에 띄워질 프론트엔드(React) 앱**을 개발하기 위한 가이드입니다.

---

## 1. 프로젝트 개요: 우리가 만드는 화면의 정체

* **실행 환경:** 일반 웹 브라우저가 아니라, **'토스 포스기 앱 내부의 iframe(웹뷰)'**에서 실행됩니다.
* **목적:** 복잡한 로그인 과정 없이, 포스기 화면에 **[6자리 인증번호]**를 띄워주어 사장님이 스마트폰(웹)과 기기를 연동할 수 있게 돕는 '스위치' 역할입니다.
* **핵심 명제:** 프론트엔드는 화면만 그려줍니다. **6자리 인증번호(PIN)를 생성하는 것은 백엔드 서버의 역할**입니다.

---

## 2. 화면 작동 시나리오 (User Flow)

1. **로딩:** 사장님이 포스기에서 플러그인을 켜면 "인증번호를 불러오는 중..." 이라는 화면이 뜹니다.
2. **API 호출:** React 앱이 켜지자마자 백엔드 서버로 `POST /api/v1/auth/pin/generate` 요청을 보냅니다.
3. **화면 표시:** 백엔드에서 생성해 준 `482910` 같은 6자리 번호를 화면 한가운데 아주 크게 띄웁니다.
4. **타이머:** 번호 밑에 **03:00** 부터 1초씩 줄어드는 타이머가 작동합니다.
5. **만료 (예외 처리):** 3분이 지나면 번호를 가리고 **[시간 초과: 번호 다시 발급받기]** 버튼을 띄워줍니다.

---

## 3. 프론트엔드 기술 스택 및 개발 세팅

* **프레임워크:** React (Vite 기반)
* **스타일링:** 순수 CSS 또는 Styled-components / Tailwind (작업자 편의에 맞게 선택)
* **로컬 서버 세팅 (포트):** 기본 `5173` 포트 사용

> **💡 로컬 테스트 주의사항 (ngrok)**
> 포스기 환경과 통신하기 위해서는 로컬 `localhost` 주소를 외부로 열어주는 `ngrok` 터널링이 필수입니다. 백엔드 팀이 공유해 준 `ngrok` 도메인을 `API_BASE_URL`로 설정하고 개발을 진행해 주세요.

---

## 4. 핵심 UI 코드 예시 (App.jsx)

이 프로젝트의 목적을 한눈에 파악할 수 있는 가장 단순화된 컴포넌트 구조입니다. (UI 디자인은 5060 시니어 타겟에 맞춰 **글씨를 크고 고대비**로 작업해 주세요.)

```jsx
import { useState, useEffect } from 'react';

export default function PosPluginApp() {
  const [pin, setPin] = useState(null);
  const [timeLeft, setTimeLeft] = useState(180); // 180초 = 3분
  const [status, setStatus] = useState('LOADING'); // LOADING, SUCCESS, EXPIRED, ERROR

  // 1. 핀 번호 발급 API 호출 함수
  const fetchPinNumber = async () => {
    setStatus('LOADING');
    try {
      // ⚠️ 실제 개발 시에는 백엔드 API 주소로 변경
      const response = await fetch('[https://api.matketing.com/api/v1/auth/pin/generate](https://api.matketing.com/api/v1/auth/pin/generate)', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          merchant_id: "toss_store_123", // 차후 토스 SDK에서 받아올 값
          toss_token: "mock_token"
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setPin(data.pin);
        setTimeLeft(180); // 타이머 3분 초기화
        setStatus('SUCCESS');
      } else {
        setStatus('ERROR');
      }
    } catch (error) {
      setStatus('ERROR');
    }
  };

  // 2. 컴포넌트 마운트 시 최초 1회 발급
  useEffect(() => {
    fetchPinNumber();
  }, []);

  // 3. 타이머 로직
  useEffect(() => {
    if (status !== 'SUCCESS' || timeLeft <= 0) {
      if (timeLeft === 0) setStatus('EXPIRED');
      return;
    }
    const timerId = setInterval(() => setTimeLeft((prev) => prev - 1), 1000);
    return () => clearInterval(timerId); // 클린업
  }, [timeLeft, status]);

  // 시간을 00:00 포맷으로 변환
  const formatTime = (seconds) => {
    const m = String(Math.floor(seconds / 60)).padStart(2, '0');
    const s = String(seconds % 60).padStart(2, '0');
    return `${m}:${s}`;
  };

  // 렌더링 화면
  return (
    <div style={{ textAlign: 'center', padding: '50px', fontFamily: 'sans-serif' }}>
      <h1 style={{ fontSize: '24px', color: '#333' }}>스마트폰에서 연동 번호를 입력해주세요</h1>
      
      {status === 'LOADING' && <p style={{ fontSize: '20px' }}>번호를 불러오는 중...</p>}
      
      {status === 'SUCCESS' && (
        <>
          <div style={{ fontSize: '64px', fontWeight: 'bold', letterSpacing: '8px', margin: '30px 0', color: '#3182f6' }}>
            {pin}
          </div>
          <p style={{ fontSize: '24px', color: '#e53e3e' }}>남은 시간: {formatTime(timeLeft)}</p>
        </>
      )}

      {(status === 'EXPIRED' || status === 'ERROR') && (
        <>
          <p style={{ fontSize: '20px', color: 'red' }}>
            {status === 'EXPIRED' ? '인증 시간이 초과되었습니다.' : '번호를 불러오는데 실패했습니다.'}
          </p>
          <button 
            onClick={fetchPinNumber}
            style={{ padding: '15px 30px', fontSize: '20px', backgroundColor: '#333', color: '#fff', borderRadius: '8px' }}
          >
            번호 다시 발급받기
          </button>
        </>
      )}
    </div>
  );
}

5. 백엔드 통신 API 명세서
프론트엔드에서 호출해야 할 API 규격입니다.

[인증번호(PIN) 발급 요청]
Method: POST

URL: /api/v1/auth/pin/generate

Request Body:
```JSON
{
  "merchant_id": "포스기에서_추출한_ID",
  "toss_token": "포스기에서_추출한_토큰"
}
```

Response Body:
```JSON
{
  "pin": "482910",
  "expires_in": 180
}
```
