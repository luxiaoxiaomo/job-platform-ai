const LOGIN_HASH_PATH = '/#/login'

function readUser() {
  try {
    const raw = localStorage.getItem('user_info')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function hasToken() {
  return !!localStorage.getItem('access_token')
}

function clearAuth() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_info')
}

function redirectToLogin() {
  clearAuth()
  window.location.href = LOGIN_HASH_PATH
}

export const authProvider = {
  async checkAuth() {
    const user = readUser()
    if (!hasToken() || !user) {
      redirectToLogin()
      return Promise.reject()
    }
    if (user.role !== 'admin') {
      return Promise.reject(new Error('需要管理员权限'))
    }
    return Promise.resolve()
  },

  async checkError(error) {
    const status = error?.status || error?.response?.status
    if (status === 401 || status === 403) {
      redirectToLogin()
      return Promise.reject()
    }
    return Promise.resolve()
  },

  async getIdentity() {
    const user = readUser()
    if (!user) {
      return Promise.reject(new Error('未登录'))
    }
    return Promise.resolve({
      id: user.id,
      fullName: user.display_name || user.phone || 'admin',
      role: user.role,
    })
  },

  async getPermissions() {
    const user = readUser()
    return Promise.resolve(user?.role || 'guest')
  },

  async logout() {
    redirectToLogin()
    return Promise.resolve()
  },

  async login() {
    return Promise.resolve()
  },
}
