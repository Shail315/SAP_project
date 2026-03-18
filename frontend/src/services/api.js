import axios from "axios";

const api = axios.create({
  baseURL: "https://fictional-system-97j7p77jq47xf6rp-8000.app.github.dev/",
  withCredentials: true
});

export default api;
