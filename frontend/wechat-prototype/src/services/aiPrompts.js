import { get, post } from './api.js'

export async function getActivePromptConfig(scenarioKey = 'job_content_review') {
  return get('/api/v1/ai-prompts/active', { scenario_key: scenarioKey })
}

export async function listPromptConfigs(scenarioKey = 'job_content_review') {
  return get('/api/v1/ai-prompts', { scenario_key: scenarioKey })
}

export async function createPromptConfig(data) {
  return post('/api/v1/ai-prompts', data)
}

export async function publishPromptConfig(configId) {
  return post(`/api/v1/ai-prompts/${configId}/publish`)
}

export async function testPromptConfig(data) {
  return post('/api/v1/ai-prompts/test', data)
}

export async function preReviewJobContent(data) {
  return post('/api/v1/ai-prompts/job-content-review', data)
}
