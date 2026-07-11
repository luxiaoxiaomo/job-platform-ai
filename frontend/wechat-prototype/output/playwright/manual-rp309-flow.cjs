const path = require('path')

let chromium
try {
  chromium = require('playwright').chromium
} catch {
  chromium = require('D:/tmp/pwmanual/node_modules/playwright').chromium
}

const API = 'http://127.0.0.1:8003'
const APP = 'http://127.0.0.1:5174'
const OUT = 'D:/AIposition/frontend/wechat-prototype/output/playwright'

async function api(apiPath, options = {}) {
  const response = await fetch(`${API}${apiPath}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(options.headers || {}),
    },
  })
  const text = await response.text()
  let json = {}
  try {
    json = text ? JSON.parse(text) : {}
  } catch {
    json = { raw: text }
  }
  if (!response.ok) {
    throw new Error(`${options.method || 'GET'} ${apiPath} failed ${response.status}: ${text}`)
  }
  return json
}

async function adminToken() {
  const login = await api('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ phone: '13700137001', password: 'Admin1234' }),
  })
  return login.access_token
}

async function endRunningExperiments(admin) {
  const experiments = await api('/api/v1/matches/rule-experiments?limit=100', {
    headers: { Authorization: `Bearer ${admin}` },
  })
  for (const experiment of experiments.items || []) {
    if (experiment.status !== 'running') {
      continue
    }
    await api(`/api/v1/matches/rule-experiments/${experiment.id}/status`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${admin}` },
      body: JSON.stringify({ status: 'ended', reason: 'R-P3-09 browser pre-clean' }),
    })
  }
}

async function createTestingRule(admin, source, name) {
  const response = await api(`/api/v1/matches/rule-configs/${source.id}/versions`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${admin}` },
    body: JSON.stringify({
      name,
      description: 'R-P3-09 browser acceptance rule',
      status: 'testing',
      scope: source.scope,
      template_key: source.template_key,
      template_name: source.template_name,
      dimensions: source.dimensions.map(item => ({
        key: item.key,
        label: item.label,
        weight: item.key === 'skill' ? 43 : Number(item.configured_weight),
        enabled: item.enabled,
        description: item.description,
        scoring_method: item.scoring_method,
        logic: item.logic,
        sort_order: item.sort_order,
      })),
    }),
  })
  return response.config
}

async function main() {
  const admin = await adminToken()
  await endRunningExperiments(admin)

  const rules = await api('/api/v1/matches/rule-configs?limit=100', {
    headers: { Authorization: `Bearer ${admin}` },
  })
  const active = (rules.items || []).find(rule => (
    rule.scope === 'global' && rule.template_key === 'default' && rule.status === 'active'
  ))
  if (!active) {
    throw new Error('No active default rule found')
  }

  const suffix = Date.now()
  const releaseRule = await createTestingRule(admin, active, `R-P3-09 Browser Release ${suffix}`)
  const releaseCheck = await api(`/api/v1/matches/rule-configs/${releaseRule.id}/release-check`, {
    headers: { Authorization: `Bearer ${admin}` },
  })
  if (!releaseCheck.can_publish) {
    throw new Error(`Release check should be publishable: ${JSON.stringify(releaseCheck)}`)
  }

  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  })
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
  await page.goto(APP)
  await page.evaluate((accessToken) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('user_info', JSON.stringify({ id: 1, role: 'admin', display_name: 'R-P3-09 Admin' }))
  }, admin)

  await page.goto(`${APP}/#/admin-ra/match-rules/${releaseRule.id}/release`)
  await page.getByRole('heading', { name: 'Release Governance', exact: true }).waitFor({ timeout: 15000 })
  await page.getByText(releaseRule.name).waitFor({ timeout: 15000 })
  await page.getByText('Can publish').waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp309-release-check.png'), fullPage: true })

  await page.getByRole('button', { name: /Publish Active/i }).click()
  await page.waitForURL(/#\/admin-ra\/match-rules\/\d+\/show/, { timeout: 15000 })
  await page.getByRole('heading', { name: releaseRule.name, exact: true }).waitFor({ timeout: 15000 })
  await page.getByText('Active').first().waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp309-published-rule.png'), fullPage: true })

  const published = await api(`/api/v1/matches/rule-configs/${releaseRule.id}`, {
    headers: { Authorization: `Bearer ${admin}` },
  })
  if (published.status !== 'active') {
    throw new Error(`Rule was not published: ${JSON.stringify(published)}`)
  }
  const publishAudits = await api(`/api/v1/matches/rule-operation-audits?resource_type=rule_config&resource_id=${releaseRule.id}`, {
    headers: { Authorization: `Bearer ${admin}` },
  })
  if (!publishAudits.items?.some(item => item.action === 'publish_rule')) {
    throw new Error(`Publish audit missing: ${JSON.stringify(publishAudits)}`)
  }

  const treatmentRule = await createTestingRule(admin, published, `R-P3-09 Browser Treatment ${suffix}`)
  const experiment = await api('/api/v1/matches/rule-experiments', {
    method: 'POST',
    headers: { Authorization: `Bearer ${admin}` },
    body: JSON.stringify({
      name: `R-P3-09 Browser Experiment ${suffix}`,
      description: 'R-P3-09 browser lifecycle acceptance',
      scope: published.scope,
      template_key: published.template_key,
      status: 'draft',
      traffic_percent: 50,
      control_config_id: Number(published.id),
      treatment_config_id: Number(treatmentRule.id),
      audience: {},
    }),
  })

  await page.goto(`${APP}/#/admin-ra/rule-experiments`)
  await page.getByText('Gray / AB Test Entry').waitFor({ timeout: 15000 })
  await page.getByText(experiment.name).waitFor({ timeout: 15000 })

  let row = page.getByRole('row').filter({ hasText: experiment.name })
  await row.getByRole('button', { name: /^Run$/i }).click()
  await page.getByText('Experiment running').waitFor({ timeout: 15000 })

  row = page.getByRole('row').filter({ hasText: experiment.name })
  await row.getByRole('button', { name: /^Pause$/i }).click()
  await page.getByText('Experiment paused').waitFor({ timeout: 15000 })

  row = page.getByRole('row').filter({ hasText: experiment.name })
  await row.getByRole('button', { name: /^Run$/i }).click()
  await page.getByText('Experiment running').waitFor({ timeout: 15000 })

  row = page.getByRole('row').filter({ hasText: experiment.name })
  await row.getByRole('button', { name: /^End$/i }).click()
  await page.getByText('Experiment ended').waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp309-experiment-actions.png'), fullPage: true })

  const experimentAudits = await api(`/api/v1/matches/rule-operation-audits?resource_type=rule_experiment&resource_id=${experiment.id}`, {
    headers: { Authorization: `Bearer ${admin}` },
  })
  const actions = (experimentAudits.items || []).map(item => item.action)
  for (const required of ['pause_experiment', 'resume_experiment', 'end_experiment']) {
    if (!actions.includes(required)) {
      throw new Error(`Experiment audit ${required} missing: ${JSON.stringify(experimentAudits)}`)
    }
  }

  await browser.close()
  console.log(JSON.stringify({
    ok: true,
    publishedRuleId: published.id,
    experimentId: experiment.id,
    publishAuditTotal: publishAudits.total,
    experimentActions: actions,
    screenshots: [
      'rp309-release-check.png',
      'rp309-published-rule.png',
      'rp309-experiment-actions.png',
    ],
  }))
}

main().catch(error => {
  console.error(error)
  process.exit(1)
})
