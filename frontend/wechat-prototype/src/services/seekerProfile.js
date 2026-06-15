import { get, put } from './api.js'

export async function getMySeekerProfile() {
  return get('/api/v1/seeker-profiles/me')
}

export async function saveMySeekerProfile(data) {
  return put('/api/v1/seeker-profiles/me', data)
}
