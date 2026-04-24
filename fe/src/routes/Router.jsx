import { createBrowserRouter } from 'react-router-dom'
import App from '../App.jsx'
import LandingPage from '../pages/landing/LandingPage.jsx'
import HomePage from '../pages/home/HomePage.jsx'
import PostCreatePage from '../pages/postCreate/PostCreatePage.jsx'
import MyPage from '../pages/mypage/MyPage.jsx'
import AuthPage from '../pages/auth/AuthPage.jsx'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: 'home', element: <HomePage /> },
      { path: 'post-create', element: <PostCreatePage /> },
      { path: 'mypage', element: <MyPage /> },
      { path: 'auth', element: <AuthPage /> },
    ],
  },
  {
    path: '*',
    element: <div>Not Found</div>,
  },
])
