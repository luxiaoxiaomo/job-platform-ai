import { API_BASE_URL, get, post } from './api.js'

export async function createApplication(data) {
  return post('/api/v1/applications', data)
}

export async function listMyApplications(params = {}) {
  return get('/api/v1/applications/me', params)
}

export async function listRecruiterApplications(params = {}) {
  return get('/api/v1/applications/recruiter', params)
}

export async function getRecruiterApplication(applicationId) {
  return get(`/api/v1/applications/recruiter/${applicationId}`)
}

export async function getMyApplication(applicationId) {
  return get(`/api/v1/applications/me/${applicationId}`)
}

export async function listApplicationsForAdmin(params = {}) {
  return get('/api/v1/applications/admin', params)
}

export async function updateApplicationStatus(applicationId, data) {
  return post(`/api/v1/applications/${applicationId}/status`, data)
}

export async function fetchRecruiterApplicationResumeFile(applicationId) {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`${API_BASE_URL}/api/v1/applications/recruiter/${applicationId}/resume-file`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  if (response.status === 401) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    window.location.href = '/#/login'
    throw new Error('未授权，请重新登录')
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || error.message || `简历文件获取失败 (${response.status})`)
  }

  const disposition = response.headers.get('content-disposition') || ''
  const match = disposition.match(/filename\*?=(?:UTF-8''|")?([^";]+)/i)
  const fileName = match ? decodeURIComponent(match[1].replace(/"/g, '')) : `application-${applicationId}-resume`
  return {
    blob: await response.blob(),
    fileName,
  }
}
