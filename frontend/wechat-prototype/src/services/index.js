/**
 * 服务层统一导出
 * 根据环境变量切换Mock/Real模式
 */

export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// 认证服务
import * as realAuthService from './auth.js'
import * as mockAuthService from './mock.js'

export const authService = USE_MOCK ? mockAuthService : realAuthService

// 用户服务
import * as realUserService from './user.js'
export * from './companyCertification.js'
export * from './jobs.js'
export * from './aiPrompts.js'
export * from './applications.js'
export * from './resumes.js'
export * from './seekerProfile.js'
export * from './matches.js'
export * from './matchRules.js'
export * from './messages.js'
export * from './notifications.js'
export * from './users.js'
export * from './baseData.js'

export const userService = USE_MOCK ? {
  getCurrentUserInfo: mockAuthService.getCurrentUserInfo,
  updateCurrentUser: mockAuthService.updateCurrentUser,
  getUserById: mockAuthService.getUserById,
} : realUserService

// 导出常用方法
export const {
  sendVerificationCode,
  register,
  login,
  logout,
  getCurrentUser,
  isAuthenticated,
} = authService

export const {
  getCurrentUserInfo,
  updateCurrentUser,
  getUserById,
} = userService
