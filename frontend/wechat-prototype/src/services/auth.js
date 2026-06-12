/**
 * 认证服务 - 真实API
 */
import { get, post } from './api.js'

/**
 * 发送验证码
 * @param {string} phone - 手机号
 * @returns {Promise<{message: string, code?: string}>}
 */
export async function sendVerificationCode(phone) {
  // 后端使用query parameter
  return post(`/api/v1/auth/send-verification-code?phone=${encodeURIComponent(phone)}`)
}

/**
 * 用户注册
 * @param {object} data - 注册数据
 * @param {string} data.phone - 手机号
 * @param {string} data.password - 密码
 * @param {string} data.display_name - 显示名称
 * @param {string} data.role - 角色（seeker/recruiter）
 * @param {string} data.verification_code - 验证码
 * @returns {Promise<{access_token: string, token_type: string, user: object}>}
 */
export async function register(data) {
  const response = await post('/api/v1/auth/register', data)

  // 保存token和用户信息
  if (response.access_token) {
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('user_info', JSON.stringify(response.user))
  }

  return response
}

/**
 * 用户登录
 * @param {string} phone - 手机号
 * @param {string} password - 密码
 * @returns {Promise<{access_token: string, token_type: string, user: object}>}
 */
export async function login(phone, password) {
  const response = await post('/api/v1/auth/login', { phone, password })

  // 保存token和用户信息
  if (response.access_token) {
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('user_info', JSON.stringify(response.user))
  }

  return response
}

/**
 * 登出
 */
export function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_info')
  // 支持HashRouter
  window.location.href = '/#/login'
}

/**
 * 获取当前用户信息（从localStorage）
 * @returns {object|null}
 */
export function getCurrentUser() {
  const userInfo = localStorage.getItem('user_info')
  return userInfo ? JSON.parse(userInfo) : null
}

/**
 * 检查是否已登录
 * @returns {boolean}
 */
export function isAuthenticated() {
  return !!localStorage.getItem('access_token')
}
