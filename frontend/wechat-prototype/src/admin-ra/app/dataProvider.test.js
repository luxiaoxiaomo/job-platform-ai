import { beforeEach, describe, expect, it, vi } from 'vitest'

import { dataProvider } from './dataProvider.js'

function jsonResponse(payload) {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('intelligent strategy dataProvider', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('access_token', 'admin-token')
    vi.restoreAllMocks()
  })

  it('maps list pagination and filters to the backend contract', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ items: [{ id: 1 }], total: 1 }))

    await expect(dataProvider.getList('intelligent-strategies', {
      pagination: { page: 2, perPage: 10 },
      filter: { status: 'draft', base_rule_config_id: '9' },
    })).resolves.toEqual({ data: [{ id: 1 }], total: 1 })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/api/v1/matches/intelligent/strategies?')
    expect(url).toContain('skip=10')
    expect(url).toContain('limit=10')
    expect(url).toContain('status=draft')
    expect(url).toContain('base_rule_config_id=9')
    expect(options.headers.get('Authorization')).toBe('Bearer admin-token')
  })

  it('maps create form fields to the intelligent strategy payload', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ id: 12, name: 'Hybrid' }))

    await dataProvider.create('intelligent-strategies', {
      data: {
        name: 'Hybrid',
        base_rule_config_id: '3',
        vector_recall_enabled: true,
        vector_recall_top_n: '50',
        vector_recall_min_similarity: '0.7',
        rule_score: 0.6,
        vector_score: 0.3,
        profile_coverage_score: 0.1,
        behavior_quality_score: 0,
      },
    })

    const [, options] = fetchMock.mock.calls[0]
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toMatchObject({
      name: 'Hybrid',
      base_rule_config_id: 3,
      vector_recall: { enabled: true, top_n: 50, min_similarity: 0.7 },
      hybrid_weights: { rule_score: 0.6, vector_score: 0.3, profile_coverage_score: 0.1, behavior_quality_score: 0 },
    })
  })

  it('maps evaluation actions to the strategy evaluation endpoint', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ id: 21 }))

    await expect(dataProvider.runIntelligentEvaluation(5, { sample_set_id: 4 })).resolves.toEqual({ id: 21 })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toMatch(/\/intelligent\/strategies\/5\/evaluations$/)
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ sample_set_id: 4 })
  })
})
