const BASE = '/api'

async function request(method, path, body = null, isFile = false) {
  const opts = { method, headers: {} }
  if (body && !isFile) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  } else if (body && isFile) {
    opts.body = body // FormData
  }
  const res = await fetch(`${BASE}${path}`, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

// Upload
export const uploadFile = (formData) => request('POST', '/upload', formData, true)
export const getUploadStatus = (videoId) => request('GET', `/upload/${videoId}/status`)
export const listVideos = () => request('GET', '/videos')
export const getVideo = (videoId) => request('GET', `/videos/${videoId}`)

// Generate
export const generatePackage = (videoId) => request('POST', `/generate/${videoId}`)
export const getPackage = (videoId) => request('GET', `/generate/${videoId}/package`)

// Dashboard
export const getAnalytics = (videoId) => request('GET', `/dashboard/${videoId}/analytics`)
export const linkYouTube = (videoId, youtubeVideoId) =>
  request('POST', `/dashboard/${videoId}/link-youtube`, { youtube_video_id: youtubeVideoId })
export const getComments = (videoId, status = null) =>
  request('GET', `/dashboard/${videoId}/comments${status ? `?status=${status}` : ''}`)
export const approveComment = (videoId, commentId, replyText) =>
  request('POST', `/dashboard/${videoId}/comments/${commentId}/approve`, { reply_text: replyText })
export const skipComment = (videoId, commentId) =>
  request('POST', `/dashboard/${videoId}/comments/${commentId}/skip`)
export const batchApproveComments = (videoId) =>
  request('POST', `/dashboard/${videoId}/comments/batch-approve`)
export const createAlert = (videoId, conditionType, thresholdValue) =>
  request('POST', `/dashboard/${videoId}/alerts`, { condition_type: conditionType, threshold_value: thresholdValue })
export const getAlerts = (videoId) => request('GET', `/dashboard/${videoId}/alerts`)
export const deleteAlert = (videoId, alertId) => request('DELETE', `/dashboard/${videoId}/alerts/${alertId}`)
export const getNotifications = (videoId = null) =>
  request('GET', `/notifications${videoId ? `?video_id=${videoId}` : ''}`)
export const markNotificationRead = (notifId) => request('POST', `/notifications/${notifId}/read`)

// Clips
export const detectClips = (videoId) => request('POST', `/clips/${videoId}/detect`)
export const getClips = (videoId) => request('GET', `/clips/${videoId}`)
export const updateClip = (videoId, clipId, status, scheduledFor = null) =>
  request('PATCH', `/clips/${videoId}/${clipId}`, { status, scheduled_for: scheduledFor })
