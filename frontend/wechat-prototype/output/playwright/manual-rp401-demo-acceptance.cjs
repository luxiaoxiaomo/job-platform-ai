const fs = require('fs')
const path = require('path')

let chromium
try {
  chromium = require('playwright').chromium
} catch {
  chromium = require('D:/tmp/pwmanual/node_modules/playwright').chromium
}

const API = process.env.API_BASE_URL || 'http://127.0.0.1:8004'
const APP = process.env.APP_BASE_URL || 'http://127.0.0.1:5174'
const OUT = 'D:/AIposition/frontend/wechat-prototype/output/playwright'
const SEED_PATH = path.join(OUT, 'rp401-demo-seed.json')

function readSeed() {
  if (!fs.existsSync(SEED_PATH)) {
    throw new Error(`Seed file not found: ${SEED_PATH}. Run backend/job-platform/scripts/seed_rp401_demo.py first.`)
  }
  return JSON.parse(fs.readFileSync(SEED_PATH, 'utf8'))
}

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

async function adminToken(seed) {
  const login = await api('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ phone: seed.admin.phone, password: seed.admin.password }),
  })
  return login.access_token
}

function requireCondition(condition, message, details) {
  if (!condition) {
    throw new Error(`${message}${details ? `: ${JSON.stringify(details)}` : ''}`)
  }
}

async function main() {
  const seed = readSeed()
  const admin = await adminToken(seed)
  const query = new URLSearchParams({
    experiment_id: String(seed.experiment_id),
    position_category: seed.position_category,
    segment_type: 'city',
  })
  const quality = await api(`/api/v1/matches/quality/summary?${query.toString()}`, {
    headers: { Authorization: `Bearer ${admin}` },
  })

  const riskSegment = quality.segments.find(item => item.segment_key === seed.risk_city)
  const healthySegment = quality.segments.find(item => item.segment_key === seed.healthy_city)
  requireCondition(quality.summary.match_count === seed.match_count, 'Unexpected RP401 match count', quality.summary)
  requireCondition(riskSegment && riskSegment.risk_level === 'high', 'Risk city segment should be high risk', riskSegment)
  requireCondition(healthySegment && healthySegment.application_rate === 100, 'Healthy city should have 100% application rate', healthySegment)
  requireCondition(
    quality.experiment_confidence?.confidence_status === seed.expected.experiment_confidence,
    'Experiment confidence mismatch',
    quality.experiment_confidence,
  )
  requireCondition(quality.anomalies.length >= seed.expected.minimum_anomalies, 'Expected RP401 anomalies', quality.anomalies)
  requireCondition(
    quality.tuning_suggestions.length >= seed.expected.minimum_suggestions,
    'Expected RP401 tuning suggestions',
    quality.tuning_suggestions,
  )
  requireCondition(
    quality.tuning_suggestions.every(item => item.guardrail.includes('Draft suggestion only')),
    'Every suggestion must show the draft-only guardrail',
    quality.tuning_suggestions,
  )

  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  })
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } })
  await page.route('http://127.0.0.1:8003/**', async (route) => {
    const request = route.request()
    const targetUrl = request.url().replace('http://127.0.0.1:8003', API)
    const response = await fetch(targetUrl, {
      method: request.method(),
      headers: request.headers(),
      body: request.postDataBuffer(),
    })
    await route.fulfill({
      status: response.status,
      headers: Object.fromEntries(response.headers.entries()),
      body: Buffer.from(await response.arrayBuffer()),
    })
  })

  await page.goto(APP)
  await page.evaluate((accessToken) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('user_info', JSON.stringify({ id: 1, role: 'admin', display_name: 'RP401 Demo Admin' }))
  }, admin)

  await page.goto(`${APP}/#/admin-ra/match-quality`)
  const mainContent = page.locator('#main-content')
  await mainContent.getByRole('heading', { name: 'Match Quality', exact: true }).waitFor({ timeout: 15000 })
  await page.getByLabel('Experiment ID').fill(String(seed.experiment_id))
  await page.getByLabel('Position Category').fill(seed.position_category)
  await page.getByRole('button', { name: /Apply/i }).click()
  await page.getByText(seed.risk_city).first().waitFor({ timeout: 15000 })
  await page.getByText('treatment_likely_better').waitFor({ timeout: 15000 })
  await page.getByText('low_application_rate').first().waitFor({ timeout: 15000 })
  await page.getByText('Draft suggestion only').first().waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp401-demo-quality-insights.png'), fullPage: true })

  await page.getByLabel('City').fill(seed.risk_city)
  await page.getByRole('button', { name: /Apply/i }).click()
  await page.waitForFunction((city) => document.body.innerText.includes(city), seed.risk_city, { timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp401-demo-risk-city-filter.png'), fullPage: true })

  await browser.close()
  console.log(JSON.stringify({
    ok: true,
    api: {
      summary: quality.summary,
      experiment_confidence: quality.experiment_confidence,
      anomalies: quality.anomalies.length,
      tuning_suggestions: quality.tuning_suggestions.length,
    },
    admin: seed.admin,
    filters: {
      experiment_id: seed.experiment_id,
      position_category: seed.position_category,
      risk_city: seed.risk_city,
    },
    screenshots: [
      'rp401-demo-quality-insights.png',
      'rp401-demo-risk-city-filter.png',
    ],
  }))
}

main().catch(error => {
  console.error(error)
  process.exit(1)
})
