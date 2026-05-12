import { useEffect, useRef, useState } from 'react';
import { TiMicrophone } from 'react-icons/ti';
import { requestSpeechToText } from '@/features/home/api/HomeApi';

function InputBar({ onTyping, disabled = false, onRecordingChange, onSubmit }) {
  const textareaRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  
  const [isExpanded, setIsExpanded] = useState(false);
  const [hasScrollbar, setHasScrollbar] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const errorTimerRef = useRef(null);

  const showError = (message) => {
    setErrorMessage(message);
    clearTimeout(errorTimerRef.current);
    errorTimerRef.current = setTimeout(() => setErrorMessage(''), 5000);
  };

  const MAX_HEIGHT = 200;

  const handleResizeHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;

      if (textarea.scrollHeight > MAX_HEIGHT) {
        setHasScrollbar(true);
      } else {
        setHasScrollbar(false);
        if (isExpanded) setIsExpanded(false);
      }
    }
  };

  useEffect(() => {
    onTyping?.(text.trim().length > 0);
  }, [text, onTyping]);

  useEffect(() => {
    return () => {
      mediaRecorderRef.current?.stream?.getTracks().forEach((track) => track.stop());
      clearTimeout(errorTimerRef.current);
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const processSpeech = async () => {
          try {
            const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
            const audioFile = new File([blob], 'recording.webm', { type: 'audio/webm' });
            const recognizedText = await requestSpeechToText(audioFile);

            if (recognizedText?.trim()) {
              setText(recognizedText);
              requestAnimationFrame(() => {
                handleResizeHeight();
              });
            }
          } catch (error) {
            showError(error.message || '음성 인식에 실패했어요. 다시 녹음해 주세요.');
          } finally {
            stream.getTracks().forEach((track) => track.stop());
          }
        };

        void processSpeech();
      };

      mediaRecorder.start();
      setIsRecording(true);
      onRecordingChange?.(true);
    } catch {
      showError('마이크 접근 권한이 필요합니다.');
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
    onRecordingChange?.(false);
  };

  const handleMicClick = () => {
    if (disabled || isSubmitting) return;

    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const isInputDisabled = disabled || isRecording || isSubmitting;

  const handleChange = (e) => {
    setText(e.target.value);
    handleResizeHeight();
  };

  const handleSubmit = async () => {
    const utterance = text.trim();
    if (!utterance || isInputDisabled) return;

    if (!onSubmit) return;

    try {
      setIsSubmitting(true);
      await onSubmit(utterance);
      setText('');
      setHasScrollbar(false);
      setIsExpanded(false);
      requestAnimationFrame(() => {
        handleResizeHeight();
      });
    } catch (error) {
      showError(error.message || '요청 처리 중 문제가 발생했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  };

  return (
    <div className="w-full px-4 pb-6">
      {/* 에러 메시지 */}
      {errorMessage && (
        <div className="mb-2 flex items-center gap-1.5 rounded-2xl bg-red-50 px-4 py-2 text-base text-red-500">
          <span className="material-icons text-base">warning</span>
          {errorMessage}
        </div>
      )}
      {/* 컨테이너 */}
      <div
        className={`relative w-full min-h-16 border rounded-4xl flex items-end p-2 transition-all duration-200 ${
          disabled
            ? 'bg-gray-200 border-gray-300 opacity-70'
            : 'bg-gray-100 border-gray-200'
        }`}
      >

        {/* 마이크 버튼 */}
        <button
          type="button"
          onClick={handleMicClick}
          aria-label={isRecording ? '녹음 중지' : '녹음 시작'}
          disabled={disabled || isSubmitting}
          className={`relative shrink-0 w-10 h-10 mb-1 ml-1 rounded-full flex items-center justify-center transition-colors duration-200 ${
            isRecording
              ? 'bg-surface-100 shadow-[0_0_10px_rgba(255,122,61,0.4)]'
              : 'bg-white border border-gray-200'
          }`}
        >
          {isRecording && (
            <span className="absolute inset-0 rounded-full animate-ping bg-primary-100 opacity-20" />
          )}
          <TiMicrophone
            className={isRecording ? 'text-primary-100' : 'text-gray-400'}
            size={20}
          />
        </button>

        {/* 텍스트 입력 영역 */}
        <textarea
          ref={textareaRef}
          value={text}
          rows={1}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={isRecording ? '음성 입력 중입니다...' : isSubmitting ? '메시지 전송 중입니다...' : '메시지를 입력하세요...'}
          disabled={isInputDisabled}
          className="w-full bg-transparent outline-none pl-2 pr-16 py-3 text-gray-700 placeholder:text-gray-400 resize-none overflow-y-auto min-h-12 disabled:cursor-not-allowed disabled:text-gray-500"
          style={{ 
            maxHeight: !disabled && isExpanded ? 'none' : `${MAX_HEIGHT}px`, 
          }}
        />

        {/* 전체화면 버튼 */}
        {!disabled && (hasScrollbar || isExpanded) && (
          <div className="absolute right-3 top-3 flex items-center group z-10">
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              disabled={disabled}
              className="w-8 h-8 rounded-full flex items-center justify-center disabled:cursor-not-allowed"
            >
              <span className="material-icons text-gray-400 text-sm">
                {isExpanded ? 'close_fullscreen' : 'open_in_full'}
              </span>
            </button>
            
            <div className="absolute right-full mr-2 top-1/2 -translate-y-1/2 px-2 py-1 rounded bg-gray-800 text-white text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              {isExpanded ? '원래대로 축소' : '전체 화면으로 펼치기'}
            </div>
          </div>
        )}

        {/* 전송 버튼 */}
        <button
          type="button"
          disabled={isInputDisabled}
          onClick={() => {
            void handleSubmit();
          }}
          className="absolute right-2 bottom-2 w-12 h-12 rounded-full bg-accent-100 flex items-center justify-center shadow-md hover:opacity-90 transition-opacity shrink-0 z-10 disabled:cursor-not-allowed disabled:bg-gray-400 disabled:shadow-none disabled:hover:opacity-100"
        >
          <span className="material-icons text-white text-xl">
            arrow_forward
          </span>
        </button>

      </div>
    </div>
  );
}

export default InputBar;
