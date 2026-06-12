/**
 * 用户服务 - 真实API
 */
import { get, put } from './api.js'

/**
 * 获取当前用户信息
 * @returns {Promise<object>}
 */
export async function getCurrentUserInfo() {
  const response = await get('/api/v1/users/me')

  // 更新localStorage中的用户信息
  localStorage.setItem('user_info', JSON.stringify(response))

  return response
}

/**
 * 更新当前用户信息
 * @param {object} data - 更新数据
 * @param {string} [data.display_name] - 显示名称
 * @param {string} [data.avatar_url] - 头像URL
 * @returns {Promise<object>}
 */
export async function updateCurrentUser(data) {
  const response = await put('/api/v1/users/me', data)

  // 更新localStorage中的用户信息
  localStorage.setItem('user_info', JSON.stringify(response))

  return response
}

/**
 * 获取指定用户信息
 * @param {number} userId - 用户ID
 * @returns {Promise<object>}
 */
export async function getUserById(userId) {
  return get(`/api/v1/users/${userId}`)
}
