import { get } from './api.js'

export async function listUsersForAdmin(params = {}) {
  return get('/api/v1/users/admin', params)
}
