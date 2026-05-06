import axios from "axios";

const baseURL = import.meta.env.DEV
  ? ""
  : import.meta.env.VITE_API_BACKEND_URL;

export const api = axios.create({
  baseURL,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});
