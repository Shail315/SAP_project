import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("metafuse_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function loginUser(payload) {
  const { data } = await api.post("/api/auth/login", payload);
  return data;
}

export async function signupUser(payload) {
  const { data } = await api.post("/api/auth/signup", payload);
  return data;
}

export async function uploadVideo(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/api/videos/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function generateMetadata(videoId) {
  const { data } = await api.post(`/api/videos/${videoId}/generate`, {
    regenerate_tags: true,
  });
  return data;
}

export async function getHistory() {
  const { data } = await api.get("/api/videos/history");
  return data;
}

export async function getVideoDetail(videoId) {
  const { data } = await api.get(`/api/videos/${videoId}`);
  return data;
}

export async function getCurrentUser() {
  const { data } = await api.get("/api/auth/me");
  return data;
}
