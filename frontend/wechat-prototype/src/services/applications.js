import { get, post } from './api.js'

export async function createApplication(data) {
  return post('/api/v1/applications', data)
}

export async function listMyApplications(params = {}) {
  return get('/api/v1/applications/me', params)
}

export async function listRecruiterApplications(params = {}) {
  return get('/api/v1/applications/recruiter', params)
}

export async function listApplicationsForAdmin(params = {}) {
  return get('/api/v1/applications/admin', params)
}

export async function updateApplicationStatus(applicationId, data) {
  return post(`/api/v1/applications/${applicationId}/status`, data)
}
