const fs = require('fs')
const path = require('path')

let chromium
try {
  chromium = require('playwright').chromium
} catch {
  chromium = require('D:/tmp/pwmanual/node_modules/playwright').chromium
}

const API = process.env.API_BASE_URL || 'http://127.0.0.1:8003'
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

function requireCondition(condition, message, details) {
  if (!condition) {
    throw new Error(`${message}${details ? `: ${JSON.stringify(details)}` : ''}`)
  }
}

async function login(seed) {
  return api('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ phone: seed.admin.phone, password: seed.admin.password }),
  })
}

async function createStrategy(token, baseRuleId) {
  const suffix = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)
  return api('/api/v1/matches/intelligent/strategies', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      name: `FE P4 browser strategy ${suffix}`,
      description: 'Browser acceptance draft for FE-P4 intelligent matching admin page.',
      base_rule_config_id: Number(baseRuleId),
      vector_recall: {
        enabled: false,
        top_n: 100,
        min_similarity: 0.62,
        candidate_source: 'job_resume_profile',
      },
      hybrid_weights: {
        rule_score: 0.85,
        vector_score: 0,
        profile_coverage_score: 0.1,
        behavior_quality_score: 0.05,
      },
      fallback_policy: 'rule_baseline',
    }),
  })
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true })
  const seed = readSeed()
  requireCondition(seed.demo_boundary?.credential_scope === 'LOCAL_DEMO_ONLY', 'Seed must be local demo scoped', seed.demo_boundary)
  const loginResult = await login(seed)
  const token = loginResult.access_token
  const user = loginResult.user
  requireCondition(token && user?.role === 'admin', 'Admin login failed', loginResult)

  const strategy = await createStrategy(token, seed.rule_config_id)
  requireCondition(strategy.id && strategy.status === 'draft', 'Strategy draft was not created', strategy)

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 1440, height: 980 } })
  await page.addInitScript(({ token, user }) => {
    window.localStorage.setItem('access_token', token)
    window.localStorage.setItem('user_info', JSON.stringify(user))
  }, { token, user })

  await page.goto(`${APP}/#/admin-ra/intelligent-matching/strategies`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)
  const initialText = await page.locator('body').innerText().catch(() => '')
  console.log(JSON.stringify({ debug_url: page.url(), debug_text: initialText.slice(0, 500) }))
  await page.screenshot({ path: path.join(OUT, 'p4-intelligent-admin-debug.png'), fullPage: true })
  await page.getByText('Intelligent Matching').first().waitFor({ timeout: 15000 })
  await page.getByText(strategy.name).waitFor({ timeout: 15000 })
  await page.getByRole('button', { name: 'Create Draft' }).waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'p4-intelligent-admin-list.png'), fullPage: true })

  await page.getByRole('button', { name: 'View' }).first().click()
  await page.waitForURL(/intelligent-matching\/strategies\/\d+/, { timeout: 15000 })
  await page.getByText('Vector Recall Config').waitFor({ timeout: 15000 })
  await page.getByText('Hybrid Weights').waitFor({ timeout: 15000 })

  await page.getByRole('button', { name: 'Run Evaluation' }).click()
  await page.getByText(/Evaluation #/).waitFor({ timeout: 15000 })
  await page.getByText(/Decision status:/).waitFor({ timeout: 15000 })
  await page.getByText(/sample_source_distribution:/).waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'p4-intelligent-admin-evaluation.png'), fullPage: true })

  await page.getByRole('button', { name: 'Clone into Draft' }).click()
  await page.waitForURL(/intelligent-matching\/strategies\/\d+\/edit/, { timeout: 15000 })
  await page.locator('#main-content').getByRole('heading', { name: 'Edit Intelligent Strategy' }).waitFor({ timeout: 15000 })
  await page.getByLabel('behavior_quality_score').waitFor({ timeout: 15000 })
  await page.getByLabel('base_rule_config_id').waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'p4-intelligent-admin-edit.png'), fullPage: true })
  await browser.close()

  console.log(JSON.stringify({
    ok: true,
    strategy_id: strategy.id,
    screenshots: [
      'p4-intelligent-admin-list.png',
      'p4-intelligent-admin-evaluation.png',
      'p4-intelligent-admin-edit.png',
    ],
  }))
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
