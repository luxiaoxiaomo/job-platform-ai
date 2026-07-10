/**
 * API Client - 统一请求封装
 */

const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8003'
export const API_BASE_URL = rawApiBaseUrl.replace('://localhost', '://127.0.0.1')

/**
 * 统一请求方法
 * @param {string} endpoint - API端点（如：/api/v1/auth/login）
 * @param {object} options - fetch选项
 * @returns {Promise<any>} 响应数据
 */
export async function request(endpoint, options = {}) {
  const { skipAuthRedirect = false, ...requestOptions } = options
  const token = localStorage.getItem('access_token')
  const isFormData = typeof FormData !== 'undefined' && requestOptions.body instanceof FormData

  const config = {
    ...requestOptions,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...requestOptions.headers,
    },
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config)

    // 401 未授权 - 清除token并跳转登录
    if (response.status === 401) {
      const error = await response.json().catch(() => ({}))
      if (skipAuthRedirect) {
        throw new Error(error.detail || error.message || '未授权，请重新登录')
      }
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_info')
      // 支持HashRouter
      window.location.href = '/#/login'
      throw new Error('未授权，请重新登录')
    }

    // 403 无权限
    if (response.status === 403) {
      throw new Error('无权限访问')
    }

    // 其他错误
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || error.message || `请求失败 (${response.status})`)
    }

    return await response.json()
  } catch (error) {
    // 网络错误或其他异常
    console.error('API请求失败:', error)
    throw error
  }
}

/**
 * GET请求
 */
export async function get(endpoint, params = {}) {
  const query = new URLSearchParams(params).toString()
  const url = query ? `${endpoint}?${query}` : endpoint
  return request(url, { method: 'GET' })
}

/**
 * POST请求
 */
export async function post(endpoint, data, options = {}) {
  return request(endpoint, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * POST multipart/form-data request.
 */
export async function postForm(endpoint, formData) {
  return request(endpoint, {
    method: 'POST',
    body: formData,
  })
}

/**
 * PUT请求
 */
export async function put(endpoint, data) {
  return request(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

/**
 * DELETE请求
 */
export async function del(endpoint) {
  return request(endpoint, { method: 'DELETE' })
}


/**
 * PATCH??
 */
export async function patch(endpoint, data) {
  return request(endpoint, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}
