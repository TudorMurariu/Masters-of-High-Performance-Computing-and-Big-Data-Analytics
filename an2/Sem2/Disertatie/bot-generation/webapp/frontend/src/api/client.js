import axios from 'axios'

const api = axios.create({ baseURL: '/api', withCredentials: true })

export const botsApi = {
  list:       ()         => api.get('/bots/').then(r => r.data),
  getById:    (id)       => api.get(`/bots/${id}`).then(r => r.data),
  get:        (id)       => api.get(`/bots/${id}`).then(r => r.data),   // alias
  byUsername: (username) => api.get(`/bots/by-username/${username}`).then(r => r.data),
  delete:     (id)       => api.delete(`/bots/${id}`).then(r => r.data),
  toggle:     (id)       => api.post(`/bots/${id}/toggle`).then(r => r.data),
}

export const generateApi = {
  bot:      (persona) => api.post('/generate/bot', { persona }).then(r => r.data),
  regenPic: (botId)   => api.post(`/generate/bot/${botId}/regen-pic`).then(r => r.data),
}

export const chatApi = {
  send:    (botId, message, sessionId) =>
    api.post(`/chat/${botId}`, { message, session_id: sessionId }).then(r => r.data),
  history: (botId, sessionId) =>
    api.get(`/chat/${botId}/history`, { params: { session_id: sessionId } }).then(r => r.data),
}

export const postsApi = {
  feed:          (page = 1)     => api.get('/posts/feed', { params: { page } }).then(r => r.data),
  forBot:        (botId)        => api.get(`/posts/bot/${botId}`).then(r => r.data),
  generate:      (botId, topic) => api.post(`/posts/generate/${botId}`, { topic }).then(r => r.data),
  generateVideo: (botId, topic) => api.post(`/posts/generate-video/${botId}`, { topic }).then(r => r.data),
  status:        (postId)       => api.get(`/posts/${postId}/status`).then(r => r.data),
  like:          (postId)       => api.post(`/posts/${postId}/like`).then(r => r.data),
  repost:        (postId)       => api.post(`/posts/${postId}/repost`).then(r => r.data),
}

export const detectApi = {
  one: (botId) => api.post(`/detect/${botId}`).then(r => r.data),
  all: ()      => api.post('/detect/all').then(r => r.data),
}

export const scheduleApi = {
  forBot: (botId)      => api.get(`/schedule/bot/${botId}`).then(r => r.data),
  create: (payload)    => api.post('/schedule/', payload).then(r => r.data),
  stop:   (scheduleId) => api.delete(`/schedule/${scheduleId}`).then(r => r.data),
}

export const authApi = {
  login:  (password) => api.post('/auth/login', { password }).then(r => r.data),
  logout: ()         => api.post('/auth/logout').then(r => r.data),
  status: ()         => api.get('/auth/status').then(r => r.data),
}

export default api
