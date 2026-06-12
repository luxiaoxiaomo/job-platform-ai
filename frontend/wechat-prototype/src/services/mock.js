/**
 * Mock服务 - 保留原型演示功能
 */

/**
 * Mock发送验证码
 * @param {string} phone - 手机号
 */
export async function sendVerificationCode(phone) {
  // 模拟网络延迟
  await new Promise(resolve => setTimeout(resolve, 500))

  return {
    message: '验证码已发送',
    code: '123456' // Mock环境返回验证码方便测试
  }
}

/**
 * Mock注册
 */
export async function register(data) {
  await new Promise(resolve => setTimeout(resolve, 800))

  const mockUser = {
    id: Math.floor(Math.random() * 10000),
    phone: data.phone,
    display_name: data.display_name,
    role: data.role,
    status: 'active',
    created_at: new Date().toISOString()
  }

  const mockToken = 'mock_token_' + Date.now()

  localStorage.setItem('access_token', mockToken)
  localStorage.setItem('user_info', JSON.stringify(mockUser))

  return {
    access_token: mockToken,
    token_type: 'bearer',
    user: mockUser
  }
}

/**
 * Mock登录
 */
export async function login(phone, password) {
  await new Promise(resolve => setTimeout(resolve, 600))

  const mockUser = {
    id: 1001,
    phone: phone,
    display_name: '测试用户',
    role: 'seeker',
    status: 'active',
    created_at: new Date().toISOString()
  }

  const mockToken = 'mock_token_' + Date.now()

  localStorage.setItem('access_token', mockToken)
  localStorage.setItem('user_info', JSON.stringify(mockUser))

  return {
    access_token: mockToken,
    token_type: 'bearer',
    user: mockUser
  }
}

/**
 * Mock登出
 */
export function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_info')
  // 支持HashRouter
  window.location.href = '/#/login'
}

/**
 * Mock获取当前用户
 */
export function getCurrentUser() {
  const userInfo = localStorage.getItem('user_info')
  return userInfo ? JSON.parse(userInfo) : null
}

/**
 * Mock检查登录状态
 */
export function isAuthenticated() {
  return !!localStorage.getItem('access_token')
}

/**
 * Mock获取当前用户信息
 */
export async function getCurrentUserInfo() {
  await new Promise(resolve => setTimeout(resolve, 300))

  const userInfo = localStorage.getItem('user_info')
  return userInfo ? JSON.parse(userInfo) : null
}

/**
 * Mock更新当前用户
 */
export async function updateCurrentUser(data) {
  await new Promise(resolve => setTimeout(resolve, 500))

  const userInfo = localStorage.getItem('user_info')
  const user = userInfo ? JSON.parse(userInfo) : {}

  const updatedUser = {
    ...user,
    ...data,
    updated_at: new Date().toISOString()
  }

  localStorage.setItem('user_info', JSON.stringify(updatedUser))

  return updatedUser
}

/**
 * Mock获取指定用户
 */
export async function getUserById(userId) {
  await new Promise(resolve => setTimeout(resolve, 300))

  return {
    id: userId,
    phone: '138****0000',
    display_name: '用户' + userId,
    role: 'seeker',
    status: 'active',
    created_at: new Date().toISOString()
  }
}
