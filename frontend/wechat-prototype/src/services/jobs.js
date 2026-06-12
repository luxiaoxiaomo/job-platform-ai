import { get, post, postForm, put } from './api.js'

export async function createJob(data) {
  return post('/api/v1/jobs/me', data)
}

export async function parseJobDescription(file) {
  const formData = new FormData()
  formData.append('file', file)
  return postForm('/api/v1/jobs/parse-jd', formData)
}

export async function parseJobDescriptionText(text) {
  return post('/api/v1/jobs/parse-jd-text', { text })
}

export async function suggestJobSalary(data) {
  return post('/api/v1/jobs/salary-suggestion', data)
}

export async function listMyJobs(params = {}) {
  return get('/api/v1/jobs/me', params)
}

export async function updateJob(jobId, data) {
  return put(`/api/v1/jobs/me/${jobId}`, data)
}

export async function listPublicJobs(params = {}) {
  return get('/api/v1/jobs/public', params)
}

export async function listJobsForAdmin(params = {}) {
  return get('/api/v1/jobs/admin', params)
}

export async function getJobForAdmin(jobId) {
  return get(`/api/v1/jobs/admin/${jobId}`)
}

export async function reviewJob(jobId, data) {
  return post(`/api/v1/jobs/admin/${jobId}/review`, data)
}
