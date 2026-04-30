import React, { useEffect, useState } from "react";
import "./App.css";
import { posPluginSdk } from "@tossplace/pos-plugin-sdk";

function App() {
  const [pinCode, setPinCode] = useState("");
  const [status, setStatus] = useState("난수 발급 중...");

  useEffect(() => {
    async function initAndRegister() {
      const randomPin = Math.floor(100000 + Math.random() * 900000).toString();
      setPinCode(randomPin);

      try {
        // 실제 POS 단말기에서 가맹점 정보 추출
        const merchant = await posPluginSdk.merchant.getMerchant();
        const merchantId = merchant.id.toString();

        // 백엔드 서버에 난수와 가맹점 식별자 전송 (accessToken 등 보안키는 프론트엔드에서 다루지 않음)
        const response = await fetch('https://myla-unrefraining-alden.ngrok-free.dev/api/register-pin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            pin: randomPin,
            merchantId: merchantId
          })
        });

        if (response.ok) {
          setStatus("등록 성공! 모바일/Postman에서 검증을 진행해주세요.");
        } else {
          setStatus("등록 실패 (서버 에러)");
        }
      } catch (error) {
        console.error("SDK 인증 정보 추출 또는 서버 등록 실패:", error);
        setStatus(`에러 발생: ${error.message || "원인 불명"}`);
      }
    }

    initAndRegister();
  }, []);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      backgroundColor: '#f8f9fa',
      fontFamily: 'sans-serif'
    }}>
      <div style={{
        padding: '40px',
        borderRadius: '16px',
        backgroundColor: '#ffffff',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        textAlign: 'center',
        width: '320px'
      }}>
        <h1 style={{ color: '#333D4B', marginBottom: '16px', fontSize: '24px' }}>인증 테스트 화면</h1>
        <p style={{ color: '#6B7684', marginBottom: '32px', fontSize: '14px' }}>
          아래 6자리 숫자를 외부 클라이언트에 입력하세요.
        </p>
        <div style={{ 
          fontSize: '48px', 
          fontWeight: 'bold', 
          letterSpacing: '8px',
          color: '#3182F6',
          marginBottom: '24px'
        }}>
          {pinCode || '------'}
        </div>
        <p style={{ color: '#8B95A1', fontSize: '12px', wordBreak: 'keep-all' }}>
          상태: {status}
        </p>
      </div>
    </div>
  );
}

export default App;
