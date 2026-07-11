import { beforeEach, describe, expect, it } from 'vitest'

import { authProvider } from './authProvider.js'

describe('admin authProvider', () => {
  beforeEach(() => {
    localStorage.clear()
    window.location.hash = ''
  })

  it('accepts an authenticated admin and exposes identity', async () => {
    localStorage.setItem('access_token', 'admin-token')
    localStorage.setItem('user_info', JSON.stringify({ id: 7, role: 'admin', display_name: 'Admin' }))

    await expect(authProvider.checkAuth()).resolves.toBeUndefined()
    await expect(authProvider.getIdentity()).resolves.toEqual({ id: 7, fullName: 'Admin', role: 'admin' })
    await expect(authProvider.getPermissions()).resolves.toBe('admin')
  })

  it('rejects a non-admin user', async () => {
    localStorage.setItem('access_token', 'seeker-token')
    localStorage.setItem('user_info', JSON.stringify({ id: 8, role: 'seeker' }))

    await expect(authProvider.checkAuth()).rejects.toThrow('需要管理员权限')
  })

  it('clears auth state on unauthorized API errors', async () => {
    localStorage.setItem('access_token', 'expired-token')
    localStorage.setItem('user_info', JSON.stringify({ id: 7, role: 'admin' }))

    await expect(authProvider.checkError({ status: 401 })).rejects.toBeUndefined()
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('user_info')).toBeNull()
  })
})
