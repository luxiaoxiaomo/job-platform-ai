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

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
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
    throw new Error(`${options.method || 'GET'} ${path} failed ${response.status}: ${text}`)
  }
  return json
}

async function ensureAdminToken() {
  const loginResponse = await api('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({
      phone: '13700137001',
      password: 'Admin1234',
    }),
  })
  return loginResponse.access_token
}

async function getRules(token) {
  return api('/api/v1/matches/rule-configs', {
    headers: { Authorization: `Bearer ${token}` },
  })
}

async function createActiveVersion(token, source) {
  const response = await api(`/api/v1/matches/rule-configs/${source.id}/versions`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      name: `R-P3-06 Browser V${Date.now()}`,
      description: 'Browser acceptance version',
      status: 'active',
      scope: source.scope,
      template_key: source.template_key,
      template_name: source.template_name,
      dimensions: source.dimensions.map(item => ({
        key: item.key,
        label: item.label,
        weight: item.key === 'skill' ? Number(item.configured_weight) + 1 : Number(item.configured_weight),
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
  const token = await ensureAdminToken()
  let rules = await getRules(token)
  const source = rules.items[0]
  const active = await createActiveVersion(token, source)

  const browser = await chromium.launch({ headless: false })
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
  await page.goto(APP)
  await page.evaluate((accessToken) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('user_info', JSON.stringify({ role: 'admin', display_name: 'R-P3-06 Admin' }))
  }, token)

  await page.goto(`${APP}/#/admin-ra/match-rules`)
  await page.getByText('Template Key').waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp306-list.png'), fullPage: true })

  await page.goto(`${APP}/#/admin-ra/match-rules/${active.id}/history`)
  await page.getByText('Compare').first().waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp306-history.png'), fullPage: true })

  const compareButton = page.getByRole('button', { name: /Compare/i }).first()
  await compareButton.click()
  await page.waitForTimeout(1000)
  await page.screenshot({ path: path.join(OUT, 'rp306-compare-after-click.png'), fullPage: true })
  if (!page.url().includes('/compare/')) {
    await page.goto(`${APP}/#/admin-ra/match-rules/${active.id}/compare/${source.id}`)
  }
  await page.getByText(/Changed \d+/).first().waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp306-compare.png'), fullPage: true })

  await page.goto(`${APP}/#/admin-ra/match-rules/${active.id}/history`)
  page.once('dialog', dialog => dialog.accept())
  await page.getByRole('button', { name: /Rollback/i }).first().click()
  await page.waitForURL(/\/show/, { timeout: 15000 })
  await page.waitForTimeout(1500)
  await page.screenshot({ path: path.join(OUT, 'rp306-rollback.png'), fullPage: true })

  await page.goto(`${APP}/#/admin-ra/rule-experiments`)
  await page.getByLabel('Name').fill(`R-P3-06 AB ${Date.now()}`)
  await page.getByLabel('Traffic %').fill('25')
  await page.getByRole('button', { name: /Create Entry/i }).click()
  await page.getByText('Experiment entry created').waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp306-experiment.png'), fullPage: true })

  await browser.close()
  console.log(JSON.stringify({ ok: true, sourceId: source.id, activeId: active.id }))
}

main().catch(error => {
  console.error(error)
  process.exit(1)
})
