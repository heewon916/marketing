import { useEffect, useRef, useState } from 'react';
import jsQR from 'jsqr';

function QRScanner({ onSuccess, disabled = false }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const streamRef = useRef(null);
  const detectedRef = useRef(false);

  const [error, setError] = useState(null);
  const [scanned, setScanned] = useState(false);

  useEffect(() => {
    if (disabled) return;

    let isMounted = true;

    const stopCamera = () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };

    const scan = () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;

      if (
        !isMounted ||
        disabled ||
        detectedRef.current ||
        !video ||
        !canvas
      ) {
        return;
      }

      if (video.readyState !== video.HAVE_ENOUGH_DATA) {
        animationRef.current = requestAnimationFrame(scan);
        return;
      }

      const ctx = canvas.getContext('2d', {
        willReadFrequently: true,
      });

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const code = jsQR(imageData.data, imageData.width, imageData.height);

      if (code?.data) {
        detectedRef.current = true;
        setScanned(true);
        stopCamera();
        onSuccess?.(code.data);
        return;
      }

      animationRef.current = requestAnimationFrame(scan);
    };

    const startCamera = async () => {
      try {
        setError(null);
        setScanned(false);
        detectedRef.current = false;

        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' },
        });

        if (!isMounted) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        streamRef.current = stream;

        if (videoRef.current) {
          videoRef.current.srcObject = stream;

          try {
            await videoRef.current.play();
          } catch (error) {
            if (error.name !== 'AbortError') {
              setError('카메라를 실행할 수 없습니다.');
            }
            return;
          }

          scan();
        }
      } catch {
        setError('카메라 접근 권한이 필요합니다.');
      }
    };

    startCamera();

    return () => {
      isMounted = false;
      stopCamera();
    };
  }, [onSuccess, disabled]);

  return (
    <div className="flex flex-col items-center gap-6 w-full">
      <div
        className="relative w-full rounded-2xl overflow-hidden bg-gray-100"
        style={{ aspectRatio: '1' }}
      >
        <video
          ref={videoRef}
          className="absolute inset-0 w-full h-full object-cover"
          muted
          playsInline
        />

        <canvas ref={canvasRef} className="hidden" />

        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-3/5 h-3/5 border-5 border-red-400 rounded-lg" />
        </div>

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
