import axios from 'axios';

const baseURL = import.meta.env.DEV
  ? ''
  : import.meta.env.VITE_API_BACKEND_URL;

export const api = axios.create({
  baseURL,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('accessToken');

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    const isRefreshRequest = originalRequest?.url?.includes(
      '/api/v1/users/token/refresh'
    );

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !isRefreshRequest
    ) {
      originalRequest._retry = true;

      try {
        const response = await api.post('/api/v1/users/token/refresh');

        const newAccessToken = response.data.accessToken;

        localStorage.setItem('accessToken', newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

        return api(originalRequest);
      } catch (refreshError) {
        // localStorage.removeItem('accessToken');
        // window.location.href = '/';
//
        // return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
