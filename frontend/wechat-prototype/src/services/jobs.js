import { del, get, post, postForm, put } from './api.js'

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

export async function getMyJobVisitors(jobId, params = {}) {
  return get(`/api/v1/jobs/me/${jobId}/visitors`, params)
}

export async function updateJob(jobId, data) {
  return put(`/api/v1/jobs/me/${jobId}`, data)
}

export async function submitJobForReview(jobId) {
  return post(`/api/v1/jobs/me/${jobId}/submit-review`, {})
}

export async function listPublicJobs(params = {}) {
  return get('/api/v1/jobs/public', params)
}

export async function searchJobs(params = {}) {
  return get('/api/v1/search/jobs', params)
}

export async function searchResumes(params = {}) {
  return get('/api/v1/search/resumes', params)
}

export async function getPublicJob(jobId) {
  return get(`/api/v1/jobs/public/${jobId}`)
}

export async function listMyJobHistory(params = {}) {
  return get('/api/v1/jobs/seeker/history', params)
}

export async function listMyJobFavorites(params = {}) {
  return get('/api/v1/jobs/seeker/favorites', params)
}

export async function addMyJobFavorite(jobId) {
  return post(`/api/v1/jobs/seeker/favorites/${jobId}`, {})
}

export async function removeMyJobFavorite(jobId) {
  return del(`/api/v1/jobs/seeker/favorites/${jobId}`)
}

export async function listMyJobSubscriptions(params = {}) {
  return get('/api/v1/jobs/seeker/subscriptions', params)
}

export async function listMySeekerNotifications(params = {}) {
  return get('/api/v1/jobs/seeker/notifications', params)
}

export async function createMyJobSubscription(data) {
  return post('/api/v1/jobs/seeker/subscriptions', data)
}

export async function updateMyJobSubscription(subscriptionId, data) {
  return put(`/api/v1/jobs/seeker/subscriptions/${subscriptionId}`, data)
}

export async function deleteMyJobSubscription(subscriptionId) {
  return del(`/api/v1/jobs/seeker/subscriptions/${subscriptionId}`)
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
