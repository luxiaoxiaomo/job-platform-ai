import { get, post } from './api.js'

export async function listMyNotifications(params = {}) {
  return get('/api/v1/notifications', params)
}

export async function getMyNotificationUnreadCount(params = {}) {
  return get('/api/v1/notifications/unread-count', params)
}

export async function markNotificationRead(notificationId) {
  return post(`/api/v1/notifications/${notificationId}/read`, {})
}

export async function markNotificationTypeRead(type) {
  return post(`/api/v1/notifications/types/${type}/read`, {})
}

export async function markAllNotificationsRead() {
  return post('/api/v1/notifications/read-all', {})
}

export async function listAdminNotificationPushTasks(params = {}) {
  return get('/api/v1/notifications/admin/push-tasks', params)
}

export async function updateAdminNotificationPushTaskStatus(taskId, data) {
  return post(`/api/v1/notifications/admin/push-tasks/${taskId}/status`, data)
}

export async function runAdminNotificationPushWorker(params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, value)
    }
  })
  const query = search.toString()
  return post(`/api/v1/notifications/admin/push-tasks/run-worker${query ? `?${query}` : ''}`, {})
}
