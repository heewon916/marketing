import React, { useEffect, useState, useRef } from "react";
import "./App.css";
import { posPluginSdk } from "@tossplace/pos-plugin-sdk";
import bgImage from "./assets/bg.jpg";

function App() {
  const [step, setStep] = useState('initial'); // 'initial', 'loading', 'generated', 'expired'
  const [pinCode, setPinCode] = useState("");
  const [status, setStatus] = useState("");
  const [timeLeft, setTimeLeft] = useState(180);

  const pinRef = useRef(pinCode);
  const merchantRef = useRef("");

  useEffect(() => {
    pinRef.current = pinCode;
  }, [pinCode]);

  // 배포 서버 API 주소
  const API_BASE_URL = 'https://www.maketing.co.kr';

  // 페이지 이동 (컴포넌트 언마운트) 시 PIN 폐기 처리
  useEffect(() => {
    return () => {
      if (pinRef.current && merchantRef.current) {
        const url = `${API_BASE_URL}/api/invalidate-pin`;
        const data = JSON.stringify({ pin: pinRef.current, merchantId: merchantRef.current });

        // navigator.sendBeacon을 사용하여 페이지 이동 시에도 백그라운드에서 신호 전송
        const blob = new Blob([data], { type: 'application/json' });
        navigator.sendBeacon(url, blob);
      }
    };
  }, []);

  // 타이머 로직
  useEffect(() => {
    let timerId;
    if (step === 'generated' && timeLeft > 0) {
      timerId = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (step === 'generated' && timeLeft <= 0) {
      setStep('expired');
      setStatus("만료되었습니다. 다시 발급해주세요.");
    }

    return () => {
      if (timerId) clearInterval(timerId);
    };
  }, [step, timeLeft]);

  const generatePin = async () => {
    setStep('loading');
    setStatus("번호 생성 중");
    const randomPin = Math.floor(100000 + Math.random() * 900000).toString();
    setPinCode(randomPin);
    setTimeLeft(180); // 3분 타이머 초기화

    try {
      // 로컬 테스트용 Mock 가맹점 ID 처리
      let mId = "test-merchant-123";
      try {
        const merchant = await posPluginSdk.merchant.getMerchant();
        mId = merchant.id.toString();
      } catch {
        console.warn("POS 환경이 아닙니다. 테스트용 가맹점 ID를 사용합니다.");
      }
      merchantRef.current = mId;

      const response = await fetch(`${API_BASE_URL}/api/v1/onboarding/pin/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pin: randomPin,
          merchantId: mId
        })
      });

      if (response.ok) {
        setStatus("등록 성공! 매장 관리 앱에서 아래 번호를 입력해주세요.");
        setStep('generated');
      } else {
        setStatus("등록 실패 (서버 에러)");
        setStep('initial');
      }
    } catch (error) {
      console.error("SDK 인증 정보 추출 또는 서버 등록 실패:", error);
      setStatus(`에러 발생: ${error.message || "원인 불명"}`);
      setStep('initial');
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      width: '100%',
      height: '100vh',
      backgroundImage: `url(${bgImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      boxSizing: 'border-box',
      padding: '20px'
    }}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        textAlign: 'center',
        width: '100%',
        maxWidth: '500px', // 넓이 조정
        minHeight: '460px', // 높이 고정
        backgroundColor: 'rgba(255, 255, 255, 0.85)', // 흰색 반투명 컨테이너
        backdropFilter: 'blur(12px)', // 글래스모피즘 효과
        borderRadius: '24px',
        padding: '40px',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)', // 입체감 그림자
        boxSizing: 'border-box',
        transition: 'all 0.3s ease'
      }}>
        <h1 style={{ color: '#222', margin: '0 0 12px 0', fontSize: '28px', fontWeight: 'bold' }}>
          맡케팅 서비스 연결하기
        </h1>
        
        <p style={{ color: '#666', margin: '0 0 32px 0', fontSize: '16px', lineHeight: '1.5' }}>
          포스를 연결하여<br/>사장님의 마케팅 전략을 분석, 제안해드립니다
        </p>

        {step === 'initial' && (
          <>
            {/* 3단계 UI */}
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'flex-start', marginBottom: '40px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '110px' }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FF7A3D" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                <span style={{ fontSize: '13px', color: '#222', marginTop: '8px', fontWeight: '500', width: '100%', wordBreak: 'keep-all' }}>인증 번호 생성</span>
              </div>
              <div style={{ width: '40px', borderTop: '2px dashed #EAEAEA', margin: '0 8px', marginTop: '14px' }}></div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '110px' }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FF7A3D" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8" cy="8" r="1"></circle><circle cx="12" cy="8" r="1"></circle><circle cx="16" cy="8" r="1"></circle><circle cx="8" cy="12" r="1"></circle><circle cx="12" cy="12" r="1"></circle><circle cx="16" cy="12" r="1"></circle><circle cx="8" cy="16" r="1"></circle><circle cx="12" cy="16" r="1"></circle><circle cx="16" cy="16" r="1"></circle></svg>
                <span style={{ fontSize: '13px', color: '#222', marginTop: '8px', fontWeight: '500', width: '100%', wordBreak: 'keep-all' }}>맡케팅 서비스에<br/>번호 입력</span>
              </div>
              <div style={{ width: '40px', borderTop: '2px dashed #EAEAEA', margin: '0 8px', marginTop: '14px' }}></div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '110px' }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FF7A3D" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                <span style={{ fontSize: '13px', color: '#222', marginTop: '8px', fontWeight: '500', width: '100%', wordBreak: 'keep-all' }}>서비스 연결 완료</span>
              </div>
            </div>

            <button
              onClick={generatePin}
              style={{
                width: '100%',
                height: '56px',
                borderRadius: '12px',
                backgroundColor: '#FF7A3D',
                color: '#ffffff',
                fontSize: '18px',
                fontWeight: '600',
                border: 'none',
                cursor: 'pointer',
                boxShadow: '0 4px 6px rgba(255, 122, 61, 0.2)',
                transition: 'background-color 0.2s',
                marginBottom: '12px'
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#e86a32'}
              onMouseOut={(e) => e.target.style.backgroundColor = '#FF7A3D'}
            >
              인증 번호 생성 하기
            </button>
            <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
              생성 후 맡케팅 서비스에 입력해주세요
            </p>
            {status && (
              <p style={{ color: '#de3a3a', marginTop: '16px', fontSize: '14px' }}>{status}</p>
            )}
          </>
        )}

        {step === 'loading' && (
          <div style={{
            padding: '24px',
            borderRadius: '16px',
            backgroundColor: 'rgba(249, 250, 251, 0.8)',
            color: '#8b95a1',
            fontSize: '16px',
            fontWeight: '600'
          }}>
            <span className="spinner" style={{ marginRight: '8px' }}>⏳</span> {status}
          </div>
        )}

        {step === 'generated' && (
          <>
            <p style={{ color: '#666', margin: '0 0 24px 0', fontSize: '16px', lineHeight: '1.5' }}>
              아래 6자리 숫자를 앱에 입력해주세요.<br/>
              남은 시간: <strong style={{ color: '#FF7A3D' }}>{formatTime(timeLeft)}</strong>
            </p>

            <div style={{
              backgroundColor: '#ffffff',
              border: '2px solid #EAEAEA',
              borderRadius: '16px',
              padding: '30px 0',
              marginBottom: '28px'
            }}>
              <div style={{
                fontSize: '56px',
                fontWeight: '800',
                letterSpacing: '14px',
                color: '#FF7A3D',
                textShadow: '0 2px 4px rgba(255, 122, 61, 0.15)'
              }}>
                {pinCode}
              </div>
            </div>

            <button
              onClick={generatePin}
              style={{
                width: '100%',
                height: '56px',
                borderRadius: '12px',
                backgroundColor: '#f2f4f6',
                color: '#666',
                fontSize: '16px',
                fontWeight: '600',
                border: 'none',
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#EAEAEA'}
              onMouseOut={(e) => e.target.style.backgroundColor = '#f2f4f6'}
              onFocus={(e) => e.target.style.backgroundColor = '#EAEAEA'}
              onBlur={(e) => e.target.style.backgroundColor = '#f2f4f6'}
            >
              재발급
            </button>
          </>
        )}

        {step === 'expired' && (
          <>
            <p style={{ color: '#FF7A3D', margin: '0 0 32px 0', fontSize: '16px', lineHeight: '1.5', fontWeight: '600' }}>
              {status}
            </p>

            <button
              onClick={generatePin}
              style={{
                width: '100%',
                height: '56px',
                borderRadius: '12px',
                backgroundColor: '#FF7A3D',
                color: '#ffffff',
                fontSize: '18px',
                fontWeight: '600',
                border: 'none',
                cursor: 'pointer',
                boxShadow: '0 4px 6px rgba(255, 122, 61, 0.2)',
                transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#e86a32'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#FF7A3D'}
              onFocus={(e) => e.target.style.backgroundColor = '#e86a32'}
              onBlur={(e) => e.target.style.backgroundColor = '#FF7A3D'}
            >
              재발급
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
