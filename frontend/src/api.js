import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8785",
  withCredentials: true,
});

export default api;