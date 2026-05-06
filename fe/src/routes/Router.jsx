import { createBrowserRouter } from 'react-router-dom'
import App from '../App.jsx'
import LandingPage from '../pages/landing/LandingPage.jsx'
import HomePage from '../pages/home/HomePage.jsx'
import PostCreatePage from '../pages/postCreate/PostCreatePage.jsx'
import MyPage from '../pages/mypage/MyPage.jsx'
import AuthPage from '../pages/auth/AuthPage.jsx'
import OnboardingPage from '../pages/auth/onboarding/OnboardingPage.jsx';
import AccountPage from '../pages/mypage/AccountPage.jsx';
import OperatingHoursPage from '../pages/mypage/OperatingHoursPage.jsx';
import InstagramCallbackPage from '../pages/auth/InstagramCallbackPage.jsx';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: 'home', element: <HomePage /> },
      { path: 'post-create', element: <PostCreatePage /> },
      { path: 'auth', element: <AuthPage /> },
      { path: 'auth/callback', element: <InstagramCallbackPage /> },
      { path: 'auth/onboarding', element: <OnboardingPage /> },
      { path: 'mypage', element: <MyPage /> },
      { path: 'mypage/account', element: <AccountPage /> },
      { path: 'mypage/account/hours', element: <OperatingHoursPage /> },
    ],
  },
  {
    path: '*',
    element: <div>Not Found</div>,
  },
])
