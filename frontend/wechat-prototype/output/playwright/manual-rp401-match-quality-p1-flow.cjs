const path = require('path')

let chromium
try {
  chromium = require('playwright').chromium
} catch {
  chromium = require('D:/tmp/pwmanual/node_modules/playwright').chromium
}

const API = process.env.API_BASE_URL || 'http://127.0.0.1:8004'
const APP = process.env.APP_BASE_URL || 'http://127.0.0.1:5175'
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

async function main() {
  const admin = await adminToken()
  const quality = await api('/api/v1/matches/quality/summary?segment_type=city', {
    headers: { Authorization: `Bearer ${admin}` },
  })
  for (const key of ['segments', 'experiment_confidence', 'anomalies', 'tuning_suggestions']) {
    if (!(key in quality)) {
      throw new Error(`quality P1 response missing ${key}`)
    }
  }

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
    localStorage.setItem('user_info', JSON.stringify({ id: 1, role: 'admin', display_name: 'R-P4-01 Admin' }))
  }, admin)

  await page.goto(`${APP}/#/admin-ra/match-quality`)
  const mainContent = page.locator('#main-content')
  await mainContent.getByRole('heading', { name: 'Match Quality', exact: true }).waitFor({ timeout: 15000 })
  await mainContent.getByRole('heading', { name: 'Segments', exact: true }).waitFor({ timeout: 15000 })
  await mainContent.getByRole('heading', { name: 'Experiment Confidence', exact: true }).waitFor({ timeout: 15000 })
  await mainContent.getByRole('heading', { name: 'Anomalies', exact: true }).waitFor({ timeout: 15000 })
  await mainContent.getByRole('heading', { name: 'Tuning Suggestions', exact: true }).waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp401-quality-segments.png'), fullPage: true })

  await page.getByLabel('City').fill('Shanghai')
  await page.getByRole('button', { name: /Apply/i }).click()
  await page.waitForFunction(() => {
    const text = document.body.innerText
    return text.includes('No quality segment data.') || text.includes('Shanghai')
  }, null, { timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp401-quality-anomalies-suggestions.png'), fullPage: true })

  await browser.close()
  console.log(JSON.stringify({
    ok: true,
    summary: quality.summary,
    segments: quality.segments.length,
    anomalies: quality.anomalies.length,
    suggestions: quality.tuning_suggestions.length,
    screenshots: [
      'rp401-quality-segments.png',
      'rp401-quality-anomalies-suggestions.png',
    ],
  }))
}

main().catch(error => {
  console.error(error)
  process.exit(1)
})
