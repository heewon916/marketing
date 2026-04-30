# 난수 6자리(PIN) 기반 API 인증 연동 구현 가이드

POS 화면에 표시된 6자리 난수를 이용해 외부(Postman 등)에서 해당 POS의 `merchantId`와 `accessToken`을 획득하는 흐름(Pairing/OTP 방식)의 구현 방법입니다.

## 1. 전체 아키텍처 및 통신 흐름

1. **POS 플러그인 (Frontend - Iframe)**
   - 6자리 난수(PIN)를 생성합니다.
   - 토스 POS SDK를 통해 현재 기기의 `merchantId`와 `accessToken`을 가져옵니다.
   - 백엔드 서버에 `[난수, merchantId, accessToken]` 쌍을 전송하여 임시 저장(매핑)합니다.
   - 화면에 생성된 6자리 난수를 렌더링합니다.

2. **백엔드 서버 (Backend)**
   - 플러그인으로부터 받은 `[난수, merchantId, accessToken]` 데이터를 메모리나 Redis와 같은 In-memory DB에 일정 시간(예: 3분) 동안 저장합니다.
   - 외부(Postman)에서 특정 API로 난수 코드가 포함된 요청이 오면, 저장소에서 해당 난수로 조회하여 매핑된 `merchantId`와 `accessToken`을 반환합니다.

3. **Postman (외부 클라이언트)**
   - POS 화면에 띄워진 6자리 난수를 확인합니다.
   - 백엔드의 특정 API로 난수를 Body에 담아 POST 요청을 보냅니다.
   - 응답으로 `merchantId`와 `accessToken`을 획득합니다.

---

## 2. 각 파트별 구현 상세

### 2.1. POS 플러그인 (Frontend)

`src/App.tsx` 또는 렌더링을 담당하는 컴포넌트에서 난수를 생성하고 백엔드로 등록하는 로직을 작성합니다.

```tsx
import React, { useEffect, useState } from 'react';
// SDK는 토스 플러그인 환경에 맞춰 임포트 (예시)
import { getAuthInfo } from '@tossplace/pos-plugin-sdk'; 

function App() {
  const [pinCode, setPinCode] = useState<string>('');

  useEffect(() => {
    async function initAndRegister() {
      // 1. 6자리 난수 생성 (예: 100000 ~ 999999)
      const randomPin = Math.floor(100000 + Math.random() * 900000).toString();
      setPinCode(randomPin);

      try {
        // 2. POS SDK를 통해 인증 정보 가져오기
        const authInfo = await getAuthInfo();
        const { merchantId, accessToken } = authInfo;

        // 3. 백엔드 서버에 난수와 인증 정보 매핑 등록 (임시 저장 요청)
        await fetch('https://[우리-백엔드-주소]/api/register-pin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            pin: randomPin,
            merchantId: merchantId,
            accessToken: accessToken
          })
        });
      } catch (error) {
        console.error('인증 정보 등록 실패:', error);
      }
    }

    initAndRegister();
  }, []);

  return (
    <div style={{ textAlign: 'center', marginTop: '50px' }}>
      <h1>테스트 화면</h1>
      <p>아래 6자리 숫자를 Postman에 입력하세요.</p>
      <div style={{ fontSize: '48px', fontWeight: 'bold', letterSpacing: '8px' }}>
        {pinCode || '로딩중...'}
      </div>
    </div>
  );
}

export default App;
```

### 2.2. 백엔드 서버 (Node.js / Express 예시)

백엔드에서는 난수를 Key로 하여 인증 정보를 저장하고 검증하는 API 2개를 구현해야 합니다.

```javascript
const express = require('express');
const app = express();
app.use(express.json());

// 난수와 인증 정보를 매핑하여 저장할 임시 저장소 (실제 운영 시 Redis 권장)
const pinStore = new Map();

// [API 1] POS 플러그인에서 난수와 인증 정보를 등록하는 API
app.post('/api/register-pin', (req, res) => {
  const { pin, merchantId, accessToken } = req.body;
  
  // 저장소에 저장 (3분 후 만료 처리 등 로직 추가 필요)
  pinStore.set(pin, { merchantId, accessToken });
  
  // 3분 뒤 자동 삭제 (TTL)
  setTimeout(() => {
    pinStore.delete(pin);
  }, 3 * 60 * 1000);

  res.status(200).json({ message: '등록 성공' });
});

// [API 2] Postman 등에서 난수를 입력해 인증 정보를 가져가는 API
app.post('/api/verify-pin', (req, res) => {
  const { pin } = req.body;

  if (pinStore.has(pin)) {
    const authInfo = pinStore.get(pin);
    // 보안을 위해 1회 조회 후 삭제 (One-Time 사용)
    pinStore.delete(pin);
    
    return res.status(200).json({
      success: true,
      merchantId: authInfo.merchantId,
      accessToken: authInfo.accessToken
    });
  } else {
    return res.status(404).json({
      success: false,
      message: '유효하지 않거나 만료된 PIN 번호입니다.'
    });
  }
});

app.listen(3000, () => console.log('Server running on port 3000'));
```

### 2.3. Postman 테스트 방법

위 API가 배포(혹은 ngrok 등으로 로컬 터널링)된 상태에서 Postman을 통해 다음과 같이 호출합니다.

**요청 (Request)**
- **Method**: POST
- **URL**: `https://[우리-백엔드-주소]/api/verify-pin`
- **Headers**: `Content-Type: application/json`
- **Body** (raw, JSON):
  ```json
  {
    "pin": "POS화면에_띄워진_6자리_난수"
  }
  ```

**응답 (Response)**
```json
{
  "success": true,
  "merchantId": "pos-merchant-12345",
  "accessToken": "eyJh... (생략)"
}
```

---

## 3. 구현 시 주의사항 (보안 및 UX)
- **난수 중복 방지**: 발급 전 현재 사용 중인 (만료되지 않은) PIN 코드인지 확인하는 로직이 필요할 수 있습니다.
- **유효 시간(TTL)**: 보안을 위해 난수는 생성 후 3~5분 정도의 짧은 유효시간만 가져야 합니다.
- **1회용 처리(One-Time)**: PIN 번호가 노출되어 재사용되는 것을 막기 위해 `verify-pin` API에서 응답을 성공적으로 주면 즉시 저장소에서 해당 PIN을 파기해야 합니다.
- **CORS 설정**: POS 플러그인 iframe 웹뷰에서 백엔드 API를 호출할 때 CORS 에러가 발생할 수 있으므로, 백엔드 서버에 적절한 CORS 허용 설정이 필요합니다.
