import { useEffect, useRef, useState } from 'react';

function InputBar({ onTyping, disabled = false }) {
  const textareaRef = useRef(null);
  const [text, setText] = useState('');
  
  const [isExpanded, setIsExpanded] = useState(false);
  const [hasScrollbar, setHasScrollbar] = useState(false);

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
    if (!disabled) return;

    setIsExpanded(false);
  }, [disabled]);

  const handleChange = (e) => {
    setText(e.target.value);
    handleResizeHeight();
  };

  return (
    <div className="w-full px-4 pb-6">
      {/* 컨테이너 */}
      <div
        className={`relative w-full min-h-16 border rounded-4xl flex items-end p-2 transition-all duration-200 ${
          disabled
            ? 'bg-gray-200 border-gray-300 opacity-70'
            : 'bg-gray-100 border-gray-200'
        }`}
      >

        {/* 텍스트 입력 영역 */}
        <textarea
          ref={textareaRef}
          value={text}
          rows={1}
          onChange={handleChange}
          placeholder={disabled ? '음성 입력 중입니다...' : '메시지를 입력하세요...'}
          disabled={disabled}
          className="w-full bg-transparent outline-none pl-4 pr-16 py-3 text-gray-700 placeholder:text-gray-400 resize-none overflow-y-auto min-h-12 disabled:cursor-not-allowed disabled:text-gray-500"
          style={{ 
            maxHeight: isExpanded ? 'none' : `${MAX_HEIGHT}px`, 
          }}
        />

        {/* 전체화면 버튼 */}
        {(hasScrollbar || isExpanded) && (
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
          disabled={disabled}
          className="absolute right-2 bottom-2 w-12 h-12 rounded-full bg-accent-100 flex items-center justify-center shadow-md hover:opacity-90 transition-opacity flex-shrink-0 z-10 disabled:cursor-not-allowed disabled:bg-gray-400 disabled:shadow-none disabled:hover:opacity-100"
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
