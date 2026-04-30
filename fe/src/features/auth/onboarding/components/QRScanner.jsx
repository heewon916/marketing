import { useEffect, useRef, useState } from 'react';
import jsQR from 'jsqr';

function QRScanner({ onSuccess }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const [error, setError] = useState(null);
  const [scanned, setScanned] = useState(false);

  useEffect(() => {
    let stream;

    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' },
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
          videoRef.current.onloadedmetadata = () => scan();
        }
      } catch {
        setError('카메라 접근 권한이 필요합니다.');
      }
    };

    const scan = () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas) return;

      const ctx = canvas.getContext('2d');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const code = jsQR(imageData.data, imageData.width, imageData.height);

      if (code) {
        setScanned(true);
        onSuccess?.(code.data);
        return;
      }

      animationRef.current = requestAnimationFrame(scan);
    };

    startCamera();

    return () => {
      cancelAnimationFrame(animationRef.current);
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, [onSuccess]);

  return (
    <div className="flex flex-col items-center gap-6 w-full">
      {/* 카메라 전체 영역 */}
      <div className="relative w-full rounded-2xl overflow-hidden bg-gray-100" style={{ aspectRatio: '1' }}>
        {/* 카메라 영상 */}
        <video
          ref={videoRef}
          className="absolute inset-0 w-full h-full object-cover"
          muted
          playsInline
        />
        <canvas ref={canvasRef} className="hidden" />

        {/* QR 가이드 박스 오버레이 */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-3/5 h-3/5 border-5 border-red-400 rounded-lg" />
        </div>

        {/* 인식 완료 */}
        {scanned && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50">
            <span className="text-white font-bold">인식 완료!</span>
          </div>
        )}
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}

export default QRScanner;