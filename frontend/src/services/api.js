import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

// Health
export const checkHealth = () => api.get('/api/health').then(r => r.data)

// Image recognition
export const recognizeImage = (file, mode = 'auto') => {
  const form = new FormData()
  form.append('file', file)
  form.append('mode', mode)
  return api.post('/api/recognize/image', form).then(r => r.data)
}

// Video upload
export const uploadVideo = (file, mode = 'auto') => {
  const form = new FormData()
  form.append('file', file)
  form.append('mode', mode)
  return api.post('/api/recognize/video', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  }).then(r => r.data)
}

// Job status polling
export const getJobStatus = (jobId) =>
  api.get(`/api/jobs/${jobId}`).then(r => r.data)

// Vocabulary
export const getVocabulary = (params = {}) =>
  api.get('/api/vocab', { params }).then(r => r.data)
