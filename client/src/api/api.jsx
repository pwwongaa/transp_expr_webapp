// src/api/api.js
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'; // fallback for dev

export const uploadFiles = async (formData) => {
  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });
  return response.json();
};
