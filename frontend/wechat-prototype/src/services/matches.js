import { get } from './api.js'

// R-P3-01：获取人岗匹配分析
export async function getMyJobMatch(jobId) {
  return get(`/api/v1/matches/jobs/${jobId}/me`)
}

export async function getRecruiterApplicationMatch(applicationId) {
  return get(`/api/v1/matches/applications/${applicationId}`)
}
