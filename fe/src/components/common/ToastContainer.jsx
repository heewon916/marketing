import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  MdCheckCircle,
  MdError,
  MdWarning,
  MdInfo,
  MdClose,
} from 'react-icons/md';

const toastStyles = {
  success: {
    bg: 'bg-white',
    border: 'border-gray-200',
    icon: MdCheckCircle,
    iconColor: 'text-green-600',
    text: 'text-gray-800',
  },
  error: {
    bg: 'bg-white',
    border: 'border-gray-200',
    icon: MdError,
    iconColor: 'text-red-600',
    text: 'text-gray-800',
  },
  warning: {
    bg: 'bg-white',
    border: 'border-gray-200',
    icon: MdWarning,
    iconColor: 'text-yellow-600',
    text: 'text-gray-800',
  },
  info: {
    bg: 'bg-white',
    border: 'border-gray-200',
    icon: MdInfo,
    iconColor: 'text-blue-600',
    text: 'text-gray-800',
  },
};

export default function ToastContainer() {
  const [toast, setToast] = useState(null);
  const timerRef = useRef(null);

  const handleClose = () => {
    setToast((prev) => prev && { ...prev, visible: false });
    clearTimeout(timerRef.current);

    timerRef.current = setTimeout(() => {
      setToast(null);
    }, 500);
  };

  useEffect(() => {
    const handleShowToast = (e) => {
      const { message, type = 'success', duration = 2500 } = e.detail;

      clearTimeout(timerRef.current);

      // 1. 먼저 visible: false로 마운트
      setToast({ message, type, visible: false });

      requestAnimationFrame(() => {
        setToast({ message, type, visible: true });
      });

      timerRef.current = setTimeout(() => {
        setToast((prev) => prev && { ...prev, visible: false });
      }, duration);

      timerRef.current = setTimeout(() => {
        setToast(null);
      }, duration + 500);
    };

    window.addEventListener('show-toast', handleShowToast);

    return () => {
      window.removeEventListener('show-toast', handleShowToast);
      clearTimeout(timerRef.current);
    };
  }, []);

  if (!toast) return null;

  const style = toastStyles[toast.type] || toastStyles.success;
  const Icon = style.icon;

  return createPortal(
    <div className="pointer-events-none fixed top-6 left-0 right-0 z-[9999] flex justify-center">
      <div
        className={`
          pointer-events-auto
          flex items-center gap-4
          w-max max-w-sm
          rounded-2xl border px-6 py-2
          ${style.bg} ${style.border}
          shadow-md
          transition-opacity duration-300 ease-out
          ${toast.visible ? 'opacity-100' : 'opacity-0'}
        `}
      >
        <div className="flex-shrink-0 rounded-full p-2.5">
          <Icon className={`h-6 w-6 ${style.iconColor}`} />
        </div>

        <span className={`text-sm font-medium ${style.text}`}>
          {toast.message}
        </span>

        <button
          type="button"
          onClick={handleClose}
          className="ml-2 flex-shrink-0 transition-opacity hover:opacity-70"
        >
          <MdClose className="h-5 w-5 text-gray-400" />
        </button>
      </div>
    </div>,
    document.body,
  );
}