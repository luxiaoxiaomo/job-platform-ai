import { get, post, postForm, put } from './api.js'

export async function getMyResume() {
  return get('/api/v1/resumes/me')
}

export async function uploadResume(file) {
  const formData = new FormData()
  formData.append('file', file)
  const result = await postForm('/api/v1/resumes/me/upload', formData)
  const uploadFailed = result?.upload?.status === 'failed'
  const parseFailed = result?.parse_run?.status && result.parse_run.status !== 'succeeded'
  if (uploadFailed || parseFailed) {
    throw new Error(result?.upload?.error_message || result?.parse_run?.error_message || '简历解析失败，请换一份文件重试')
  }
  if (result?.resume) {
    return {
      ...result.resume,
      upload: result.upload,
      parse_run: result.parse_run,
    }
  }
  return result
}

// R-P1-06 联调：上传历史列表
// 返回 [{ upload, latest_parse_run }]
export async function listMyUploads(limit = 20) {
  return get(`/api/v1/resumes/me/uploads?limit=${limit}`)
}

// R-P1-06 联调：解析详情（含原文预览 + chunks）
// 返回 { upload, parse_run, extracted_text, chunks }
export async function getParseRunDetail(parseRunId) {
  return get(`/api/v1/resumes/me/parse-runs/${parseRunId}`)
}

// R-P2-04：获取解析结果结构化数据
// 返回 { basic, educations, work_experiences, projects, skills, certificates }
export async function getStructuredResult(parseRunId) {
  return get(`/api/v1/resumes/me/parse-runs/${parseRunId}/structured`)
}

// R-P2-04：确认解析结果并投影到明细表
export async function confirmStructuredResult(parseRunId, data) {
  return put('/api/v1/resumes/me/structured/confirm', {
    parse_run_id: parseRunId,
    ...data
  })
}

// R-P2-05：获取画像聚合数据
export async function getProfileSummary() {
  return get('/api/v1/resumes/me/profile-summary')
}

export async function getRecruiterApplicationStructuredProfile(applicationId) {
  return get(`/api/v1/resumes/recruiter/applications/${applicationId}/structured-profile`)
}
