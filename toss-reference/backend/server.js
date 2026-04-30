const express = require('express');
const cors = require('cors');

const app = express();

// allow all cross-origin requests for testing
app.use(cors());
app.use(express.json());

// 난수와 가맹점 식별자를 매핑하여 저장할 임시 저장소 (실제 운영 시 Redis 권장)
const pinStore = new Map();

// [API 1] POS 플러그인에서 난수와 가맹점 식별자를 등록하는 API
app.post('/api/register-pin', (req, res) => {
  const { pin, merchantId } = req.body;
  
  if (!pin || !merchantId) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  // 저장소에 저장 (오직 merchantId만 저장합니다)
  pinStore.set(pin, { merchantId });
  console.log(`[등록] PIN: ${pin}, MerchantID: ${merchantId}`);
  
  // 3분 뒤 자동 삭제 (TTL)
  setTimeout(() => {
    if (pinStore.has(pin)) {
      pinStore.delete(pin);
      console.log(`[만료] PIN: ${pin} 삭제됨`);
    }
  }, 3 * 60 * 1000);

  res.status(200).json({ message: '등록 성공' });
});

// [API 2] 외부(모바일/Postman)에서 난수를 입력해 가맹점 정보를 가져가는 API
app.post('/api/verify-pin', (req, res) => {
  const { pin } = req.body;

  if (!pin) {
    return res.status(400).json({ error: 'PIN is required' });
  }

  if (pinStore.has(pin)) {
    const authInfo = pinStore.get(pin);
    
    // 보안을 위해 1회 조회 후 삭제 (One-Time 사용)
    pinStore.delete(pin);
    console.log(`[검증 성공 및 파기] PIN: ${pin}`);
    
    // 검증된 merchantId만 응답으로 보냅니다.
    // 이후 모바일 앱은 이 merchantId를 가지고 본인 인증을 마무리합니다.
    return res.status(200).json({
      success: true,
      merchantId: authInfo.merchantId
    });
  } else {
    console.log(`[검증 실패] 유효하지 않은 PIN: ${pin}`);
    return res.status(404).json({
      success: false,
      message: '유효하지 않거나 만료된 PIN 번호입니다.'
    });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Backend server running on port ${PORT}`);
  console.log(`Ngrok ACL: https://myla-unrefraining-alden.ngrok-free.dev`);
});
