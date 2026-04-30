# 실제 SDK를 활용한 merchantId & accessToken 연동 계획

제공해주신 `prompt4.md`의 내용을 바탕으로, 테스트용 더미 데이터가 아닌 **실제 토스 POS SDK**를 통해 가맹점 식별자와 액세스 토큰을 추출하고 서버와 연동하는 구현 계획입니다.

---

## 1. 프론트엔드 (POS 플러그인 - `App.jsx`) 수정 계획

현재 하드코딩된 테스트 데이터를 제거하고, SDK에서 제공하는 메서드를 호출하여 실제 데이터를 가져오도록 수정합니다.

### 📍 변경 사항
1. **가맹점 정보 추출**: `posPluginSdk.merchant.getMerchant()` (또는 `posPluginSdk.getMerchant()`)를 호출하여 `merchant.id`를 추출합니다.
2. **세션 토큰 추출**: `posPluginSdk.getAccessToken()`을 호출하여 현재 플러그인 세션을 보증하는 `accessToken`을 추출합니다.
3. **데이터 전송**: 생성된 6자리 난수와 함께 추출한 `merchantId`, `accessToken`을 묶어 백엔드(`/api/register-pin`)로 전송합니다.

### 💻 예상 코드 스니펫
```javascript
// App.jsx 내부 initAndRegister() 함수 수정

// 1. 6자리 난수 생성
const randomPin = Math.floor(100000 + Math.random() * 900000).toString();
setPinCode(randomPin);

try {
  // 2. 실제 토스 POS SDK를 통해 정보 가져오기
  // (SDK 버전에 따라 posPluginSdk.merchant.getMerchant() 또는 posPluginSdk.getMerchant() 사용)
  const merchant = await posPluginSdk.merchant.getMerchant();
  const merchantId = merchant.id.toString(); 

  const accessToken = await posPluginSdk.getAccessToken();

  // 3. 백엔드 서버에 실제 데이터 등록
  const response = await fetch('https://myla-unrefraining-alden.ngrok-free.dev/api/register-pin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pin: randomPin,
      merchantId: merchantId,
      accessToken: accessToken
    })
  });

  if (response.ok) {
    setStatus("등록 성공! Postman에서 검증을 진행해주세요.");
  } else {
    setStatus("등록 실패 (서버 에러)");
  }
} catch (error) {
  console.error("SDK 인증 정보 추출 실패:", error);
  setStatus("등록 실패 (SDK 에러)");
}
```

---

## 2. 백엔드 (`server.js`) 수정 계획

이전에는 보안상 `accessToken`을 백엔드의 환경변수(`.env`)에서 관리하는 방식을 제안드렸으나, `prompt4.md`의 가이드에 따라 **플러그인의 세션 토큰을 직접 받아 활용하는 방식**으로 원복 및 수정합니다.

### 📍 변경 사항
1. **`/api/register-pin` API**: 프론트엔드로부터 `pin`, `merchantId`와 함께 `accessToken`도 Body로 전달받도록 수정합니다.
2. **메모리 저장소**: `pin`을 Key로 하여 `merchantId`와 `accessToken`을 임시 저장소(`pinStore`)에 함께 매핑하여 저장합니다.
3. **`/api/verify-pin` API**: Postman에서 `pin`으로 검증을 요청할 때, 서버 환경변수가 아닌 프론트엔드(POS 단말)로부터 직접 전달받아 저장해두었던 **실제 `accessToken`**을 반환하도록 응답을 수정합니다.

### 💻 예상 코드 스니펫
```javascript
// server.js 내부 수정

// [API 1] 등록 API
app.post('/api/register-pin', (req, res) => {
  const { pin, merchantId, accessToken } = req.body; // accessToken 다시 추가
  
  if (!pin || !merchantId || !accessToken) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  // 저장소에 모두 저장
  pinStore.set(pin, { merchantId, accessToken });
  
  // (TTL 로직 동일) ...
  res.status(200).json({ message: '등록 성공' });
});

// [API 2] 검증 API
app.post('/api/verify-pin', (req, res) => {
  const { pin } = req.body;

  if (pinStore.has(pin)) {
    const authInfo = pinStore.get(pin);
    pinStore.delete(pin); // 1회용 파기
    
    return res.status(200).json({
      success: true,
      merchantId: authInfo.merchantId,
      accessToken: authInfo.accessToken // 프론트에서 받은 실제 토큰 반환
    });
  } else {
    return res.status(404).json({ success: false, message: '유효하지 않은 PIN' });
  }
});
```

---

## 3. 요약 및 다음 단계

위 계획대로 코드를 반영하면 더미 데이터가 완전히 걷히고, 실제 POS 단말기의 가맹점 정보와 세션 토큰이 Postman으로 전달되는 **End-to-End 연동**이 완성됩니다.

위 계획에 따라 바로 `App.jsx`와 `server.js`의 코드를 수정(구현)할까요?
