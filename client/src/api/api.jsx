// src/api/api.js
// export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'; // fallback for dev
// export const API_BASE = import.meta.env.VITE_API_BASE;
export const API_BASE =
  import.meta.env.VITE_API_BASE || "https://api.kawacloud11.org";  // fallback

//export const means it is able to be used in other files*

// export const uploadFiles = async (formData) => {
//   const response = await fetch(`${API_BASE}/upload`, {
//     method: 'POST',
//     body: formData,
//   });
//   return response.json();
// };

export const uploadFiles = async (formData) => {
  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status}`);
  }
  return response.json();
};