import { get, postForm } from './api.js'

export async function getMyResume() {
  return get('/api/v1/resumes/me')
}

export async function uploadResume(file) {
  const formData = new FormData()
  formData.append('file', file)
  return postForm('/api/v1/resumes/me/upload', formData)
}
