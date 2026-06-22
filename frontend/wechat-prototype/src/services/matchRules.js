import { get, post } from './api.js'

// R-P3-04：获取匹配规则列表
export async function listMatchRuleConfigs(params = {}) {
  const query = new URLSearchParams(params).toString()
  return get(`/api/v1/matches/rule-configs${query ? `?${query}` : ''}`)
}

// R-P3-04：获取匹配规则详情
export async function getMatchRuleConfig(id) {
  return get(`/api/v1/matches/rule-configs/${id}`)
}

// R-P3-04：获取默认匹配规则
export async function getDefaultMatchRuleConfig() {
  return get('/api/v1/matches/rule-configs/default')
}

// R-P3-04：获取规则历史版本（预留）
export async function getMatchRuleConfigHistory(id) {
  return get(`/api/v1/matches/rule-configs/${id}/history`)
}

// R-P3-05：基于当前规则保存新版本
export async function createMatchRuleConfigVersion(id, data) {
  return post(`/api/v1/matches/rule-configs/${id}/versions`, data)
}
