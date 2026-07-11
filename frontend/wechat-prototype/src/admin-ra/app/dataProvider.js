import { fetchUtils } from 'react-admin'
import { API_BASE_URL } from '../../services/api.js'

const RESOURCE_PATH = {
  'match-rules': '/api/v1/matches/rule-configs',
  'rule-experiments': '/api/v1/matches/rule-experiments',
  'intelligent-strategies': '/api/v1/matches/intelligent/strategies',
}

function getResourcePath(resource) {
  const base = RESOURCE_PATH[resource]
  if (!base) {
    throw new Error(`Unknown resource: ${resource}`)
  }
  return base
}

function buildHeaders(options = {}) {
  const headers = new Headers(options.headers || { Accept: 'application/json' })
  const token = localStorage.getItem('access_token')

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  return headers
}

const httpClient = (url, options = {}) => (
  fetchUtils.fetchJson(url, {
    ...options,
    headers: buildHeaders(options),
  })
)

function normalizeListResponse(json) {
  const data = json.items || json || []
  return {
    data,
    total: typeof json.total === 'number' ? json.total : data.length,
  }
}

function toVersionPayload(data, previousData = {}) {
  const previousDimensions = Array.isArray(previousData.dimensions) ? previousData.dimensions : []
  const currentDimensions = Array.isArray(data.dimensions) ? data.dimensions : []

  return {
    name: data.name,
    description: data.description || '',
    status: data.status || 'draft',
    scope: data.scope || previousData.scope || 'global',
    template_key: data.template_key || previousData.template_key || 'default',
    template_name: data.template_name || previousData.template_name || 'Default template',
    effective_from: data.effective_from || null,
    effective_to: data.effective_to || null,
    dimensions: currentDimensions
      .map((item, index) => {
        const previous = previousDimensions[index] || {}
        return {
          key: item.key || previous.key,
          label: item.label || previous.label || previous.key,
          weight: Number(item.weight ?? item.configured_weight ?? previous.configured_weight ?? previous.weight ?? 0),
          enabled: item.enabled ?? previous.enabled ?? true,
          description: item.description ?? previous.description ?? '',
          scoring_method: item.scoring_method ?? previous.scoring_method ?? '',
          logic: item.logic || previous.logic || {},
          sort_order: Number(item.sort_order ?? previous.sort_order ?? index),
        }
      })
      .filter(item => item.key),
  }
}

function validateVersionPayload(payload) {
  if (!payload.name?.trim()) {
    throw new Error('Please enter a rule name')
  }
  if (!payload.dimensions.length) {
    throw new Error('At least one dimension is required')
  }
  if (payload.dimensions.some(item => !item.key || !item.label)) {
    throw new Error('Dimension key and label are required')
  }
  if (!payload.dimensions.some(item => item.enabled && Number(item.weight) > 0)) {
    throw new Error('At least one enabled dimension must have a positive weight')
  }
  return payload
}

function numericValue(value, fallback = 0) {
  if (value === '' || value === undefined || value === null) return fallback
  const next = Number(value)
  return Number.isFinite(next) ? next : fallback
}

function toIntelligentStrategyPayload(data = {}) {
  const hybridWeights = {
    rule_score: numericValue(data.rule_score, 0.7),
    vector_score: numericValue(data.vector_score, 0.2),
    profile_coverage_score: numericValue(data.profile_coverage_score, 0.1),
    behavior_quality_score: numericValue(data.behavior_quality_score, 0),
  }
  const total = Object.values(hybridWeights).reduce((sum, value) => sum + value, 0)
  if (Math.abs(total - 1) > 0.001) {
    throw new Error('hybrid_weights_total_must_equal_1')
  }

  return {
    name: data.name,
    description: data.description || '',
    base_rule_config_id: Number(data.base_rule_config_id),
    vector_recall: {
      enabled: Boolean(data.vector_recall_enabled),
      top_n: numericValue(data.vector_recall_top_n, 100),
      min_similarity: numericValue(data.vector_recall_min_similarity, 0.62),
      candidate_source: data.vector_recall_candidate_source || 'job_resume_profile',
    },
    hybrid_weights: hybridWeights,
    fallback_policy: data.fallback_policy || 'rule_baseline',
  }
}

export const dataProvider = {
  async getList(resource, params) {
    const base = getResourcePath(resource)
    const { page, perPage } = params.pagination || { page: 1, perPage: 20 }
    const filter = params.filter || {}

    const query = {
      skip: (page - 1) * perPage,
      limit: perPage,
    }
    if (filter.scope) {
      query.scope = filter.scope
    }
    if (filter.template_key) {
      query.template_key = filter.template_key
    }
    if (resource === 'intelligent-strategies') {
      if (filter.status) {
        query.status = filter.status
      }
      if (filter.base_rule_config_id) {
        query.base_rule_config_id = Number(filter.base_rule_config_id)
      }
    }

    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(query).filter(([, value]) => value !== undefined && value !== ''))
    ).toString()

    const { json } = await httpClient(`${API_BASE_URL}${base}${qs ? `?${qs}` : ''}`)
    return normalizeListResponse(json)
  },

  async getOne(resource, params) {
    const base = getResourcePath(resource)
    const { json } = await httpClient(`${API_BASE_URL}${base}/${params.id}`)
    return { data: json }
  },

  async update(resource, params) {
    const base = getResourcePath(resource)
    if (resource === 'match-rules') {
      const payload = validateVersionPayload(toVersionPayload(params.data, params.previousData))
      const { json } = await httpClient(`${API_BASE_URL}${base}/${params.id}/versions`, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      return { data: json.config || json }
    }
    if (resource === 'intelligent-strategies') {
      const payload = toIntelligentStrategyPayload(params.data)
      const { json } = await httpClient(`${API_BASE_URL}${base}/${params.id}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      })
      return { data: json }
    }
    throw new Error(`Update is not supported for ${resource}`)
  },

  async getMany(resource, params) {
    const base = getResourcePath(resource)
    const data = await Promise.all(
      params.ids.map(id => httpClient(`${API_BASE_URL}${base}/${id}`).then(({ json }) => json))
    )
    return { data }
  },

  async getManyReference(resource, params) {
    if (resource !== 'match-rules') {
      return this.getList(resource, params)
    }
    const base = getResourcePath(resource)
    const { json } = await httpClient(`${API_BASE_URL}${base}/${params.id}/history`)
    return normalizeListResponse(json)
  },

  async create(resource, params) {
    const base = getResourcePath(resource)
    if (resource === 'match-rules') {
      const { json } = await httpClient(`${API_BASE_URL}${base}/templates`, {
        method: 'POST',
        body: JSON.stringify(params.data || {}),
      })
      return { data: json.config || json }
    }
    if (resource === 'intelligent-strategies') {
      const { json } = await httpClient(`${API_BASE_URL}${base}`, {
        method: 'POST',
        body: JSON.stringify(toIntelligentStrategyPayload(params.data)),
      })
      return { data: json }
    }
    const { json } = await httpClient(`${API_BASE_URL}${base}`, {
      method: 'POST',
      body: JSON.stringify(params.data || {}),
    })
    return { data: json.config || json }
  },

  async compareRuleConfigs(baseId, targetId) {
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/rule-configs/${baseId}/compare/${targetId}`)
    return json
  },

  async rollbackRuleConfig(currentId, payload) {
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/rule-configs/${currentId}/rollback`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    return json
  },

  async getRuleReleaseCheck(ruleId) {
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/rule-configs/${ruleId}/release-check`)
    return json
  },

  async publishRuleConfig(ruleId, payload) {
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/rule-configs/${ruleId}/publish`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    return json
  },

  async getRuleExperimentEffects(experimentId) {
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/rule-experiments/${experimentId}/effects`)
    return json
  },

  async updateRuleExperimentStatus(experimentId, payload) {
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/rule-experiments/${experimentId}/status`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    return json
  },

  async getMatchAudits(filter = {}) {
    const query = {
      experiment_id: filter.experiment_id,
      rule_config_id: filter.rule_config_id,
      job_id: filter.job_id,
      seeker_id: filter.seeker_id,
      experiment_bucket: filter.experiment_bucket,
      created_from: filter.created_from,
      created_to: filter.created_to,
      skip: filter.skip || 0,
      limit: filter.limit || 20,
    }
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(query).filter(([, value]) => value !== undefined && value !== null && value !== ''))
    ).toString()
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/audits${qs ? `?${qs}` : ''}`)
    return normalizeListResponse(json)
  },

  async getMatchAudit(auditId) {
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/audits/${auditId}`)
    return json
  },

  async getMatchQualitySummary(filter = {}) {
    const query = {
      experiment_id: filter.experiment_id,
      rule_config_id: filter.rule_config_id,
      scope: filter.scope,
      template_key: filter.template_key,
      created_from: filter.created_from,
      created_to: filter.created_to,
      city: filter.city,
      position_category: filter.position_category,
      standard_position_id: filter.standard_position_id,
      job_tag: filter.job_tag,
      segment_type: filter.segment_type,
      include_insights: filter.include_insights,
    }
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(query).filter(([, value]) => value !== undefined && value !== null && value !== ''))
    ).toString()
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/quality/summary${qs ? `?${qs}` : ''}`)
    return json
  },

  async cloneIntelligentStrategy(strategyId, payload) {
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/intelligent/strategies/${strategyId}/clone`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    return json
  },

  async runIntelligentEvaluation(strategyId, payload) {
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/intelligent/strategies/${strategyId}/evaluations`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    return json
  },

  async getIntelligentEvaluation(evaluationId) {
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/intelligent/evaluations/${evaluationId}`)
    return json
  },

  async getRuleOperationAudits(filter = {}) {
    const query = {
      resource_type: filter.resource_type,
      resource_id: filter.resource_id,
      action: filter.action,
      actor_id: filter.actor_id,
      skip: filter.skip || 0,
      limit: filter.limit || 20,
    }
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(query).filter(([, value]) => value !== undefined && value !== null && value !== ''))
    ).toString()
    const { json } = await httpClient(`${API_BASE_URL}/api/v1/matches/rule-operation-audits${qs ? `?${qs}` : ''}`)
    return normalizeListResponse(json)
  },

  async delete() {
    throw new Error('Delete is not supported for rule management')
  },

  async updateMany() {
    throw new Error('Bulk update is not supported for rule management')
  },

  async deleteMany() {
    throw new Error('Bulk delete is not supported for rule management')
  },
}
