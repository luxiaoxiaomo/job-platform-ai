import { beforeEach, describe, expect, it, vi } from 'vitest'

import { request } from './api.js'

describe('API request', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('adds JSON and bearer-token headers', async () => {
    localStorage.setItem('access_token', 'token-123')
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(request('/api/v1/example', { method: 'POST', body: '{}' })).resolves.toEqual({ ok: true })

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/example$/),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer token-123',
          'Content-Type': 'application/json',
        }),
      }),
    )
  })

  it('preserves auth state when a login request opts out of redirect handling', async () => {
    localStorage.setItem('access_token', 'stale-token')
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'invalid credentials' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(request('/api/v1/auth/login', { skipAuthRedirect: true })).rejects.toThrow('invalid credentials')
    expect(localStorage.getItem('access_token')).toBe('stale-token')
  })
})
