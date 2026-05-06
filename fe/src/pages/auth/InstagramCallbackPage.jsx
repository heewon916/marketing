import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { INSTAGRAM_AUTH_PURPOSE } from '@/features/auth/api.js';

function InstagramCallbackPage() {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get('token');

    const purpose =
      sessionStorage.getItem('instagramAuthPurpose') ||
      INSTAGRAM_AUTH_PURPOSE.LOGIN;

    sessionStorage.removeItem('instagramAuthPurpose');

    if (!accessToken) {
      navigate('/', { replace: true });
      return;
    }

    localStorage.setItem('accessToken', accessToken);

    window.history.replaceState({}, document.title, '/auth/callback');

    if (purpose === INSTAGRAM_AUTH_PURPOSE.ONBOARDING) {
      navigate('/auth/onboarding?instagram=success', { replace: true });
      return;
    }

    navigate('/home', { replace: true });
  }, [navigate]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-white px-6">
      <p className="text-base font-semibold text-gray-700">
        인스타그램 인증을 완료하고 있어요.
      </p>
    </main>
  );
}

export default InstagramCallbackPage;
