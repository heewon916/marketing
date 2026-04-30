import React, { useEffect, useState } from "react";
import "./App.css";
import { posPluginSdk } from "@tossplace/pos-plugin-sdk";

function App() {
  const [pinCode, setPinCode] = useState("");
  const [status, setStatus] = useState("단말기 정보 조회 중...");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function initAndRegister() {
      const randomPin = Math.floor(100000 + Math.random() * 900000).toString();
      setPinCode(randomPin);
      setStatus("백엔드 서버 연동 중...");

      try {
        // 실제 POS 단말기에서 가맹점 정보 추출
        const merchant = await posPluginSdk.merchant.getMerchant();
        const merchantId = merchant.id.toString();

        // Ngrok 등 외부에서 접근 가능한 백엔드 주소로 변경 필요
        const response = await fetch('https://www.maketing.co.kr/api/v1/onboarding/pin/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            pin: randomPin,
            merchantId: merchantId
          })
        });

        if (response.ok) {
          setStatus("등록 성공! 매장 관리 앱에서 아래 번호를 입력해주세요.");
        } else {
          setStatus("등록 실패 (서버 에러)");
        }
      } catch (error) {
        console.error("SDK 인증 정보 추출 또는 서버 등록 실패:", error);
        setStatus(`에러 발생: ${error.message || "원인 불명"}`);
      } finally {
        setIsLoading(false);
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
      minHeight: '100vh',
      backgroundColor: '#f2f4f6',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    }}>
      <div style={{
        padding: '40px',
        borderRadius: '24px',
        backgroundColor: '#ffffff',
        boxShadow: '0 8px 30px rgba(0,0,0,0.08)',
        textAlign: 'center',
        width: '360px',
        transition: 'all 0.3s ease'
      }}>
        <div style={{ marginBottom: '24px' }}>
          {/* 토스 스타일 아이콘 대체 */}
          <div style={{ 
            width: '64px', height: '64px', 
            borderRadius: '50%', backgroundColor: '#e8f3ff', 
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto', fontSize: '32px'
          }}>
            📱
          </div>
        </div>
        <h1 style={{ color: '#191f28', margin: '0 0 12px 0', fontSize: '26px', fontWeight: 'bold' }}>
          포스기 연동
        </h1>
        <p style={{ color: '#4e5968', margin: '0 0 32px 0', fontSize: '15px', lineHeight: '1.5' }}>
          매장 마케팅 자동화를 위해<br/>아래 6자리 숫자를 앱에 입력해주세요.
        </p>

        <div style={{ 
          backgroundColor: '#f9fafb',
          borderRadius: '16px',
          padding: '24px 0',
          marginBottom: '28px'
        }}>
          <div style={{ 
            fontSize: '52px', 
            fontWeight: '800', 
            letterSpacing: '12px',
            color: '#3182f6',
            textShadow: '0 2px 4px rgba(49, 130, 246, 0.2)'
          }}>
            {pinCode || '------'}
          </div>
        </div>

        <div style={{ 
          padding: '16px', 
          borderRadius: '12px', 
          backgroundColor: isLoading ? '#f2f4f6' : (status.includes('성공') ? '#e8f3ff' : '#fee5e5'),
          color: isLoading ? '#8b95a1' : (status.includes('성공') ? '#1b64da' : '#de3a3a'),
          fontSize: '14px',
          fontWeight: '600',
          wordBreak: 'keep-all',
          lineHeight: '1.4'
        }}>
          {isLoading ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
              <span className="spinner">⏳</span> {status}
            </span>
          ) : status}
        </div>
      </div>
    </div>
  );
}

export default App;
