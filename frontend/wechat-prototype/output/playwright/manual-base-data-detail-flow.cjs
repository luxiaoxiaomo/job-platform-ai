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

async function findStandardPosition(admin, name) {
  const query = new URLSearchParams({ q: name, limit: '100' })
  const data = await api(`/api/v1/base-data/standard-positions?${query.toString()}`, {
    headers: { Authorization: `Bearer ${admin}` },
  })
  return (data.items || []).find(item => item.name === name) || null
}

async function findTag(admin, name, category) {
  const query = new URLSearchParams({ q: name, category, limit: '100' })
  const data = await api(`/api/v1/base-data/tags?${query.toString()}`, {
    headers: { Authorization: `Bearer ${admin}` },
  })
  return (data.items || []).find(item => item.name === name && item.category === category) || null
}

async function createDemoData(admin) {
  const positionName = 'BD Detail Analyst Acceptance'
  const parentName = 'BD Detail Parent Acceptance'
  const tagName = 'BD Detail SQL Acceptance'
  const category = 'skill-detail'

  let position = await findStandardPosition(admin, positionName)
  if (!position) {
    position = await api('/api/v1/base-data/standard-positions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${admin}` },
      body: JSON.stringify({
        name: positionName,
        category: 'Data Ops',
        aliases: ['BD Analyst Acceptance', 'Ops Analyst Acceptance'],
        description: 'Detail page acceptance position',
      }),
    })
  }

  let parent = await findTag(admin, parentName, category)
  if (!parent) {
    parent = await api('/api/v1/base-data/tags', {
      method: 'POST',
      headers: { Authorization: `Bearer ${admin}` },
      body: JSON.stringify({
        name: parentName,
        category,
        color: '#2563eb',
        sort_order: 1,
      }),
    })
  }

  let tag = await findTag(admin, tagName, category)
  if (!tag) {
    tag = await api('/api/v1/base-data/tags', {
      method: 'POST',
      headers: { Authorization: `Bearer ${admin}` },
      body: JSON.stringify({
        name: tagName,
        category,
        parent_id: parent.id,
        color: '#16a34a',
        description: 'Detail page acceptance tag',
        sort_order: 12,
      }),
    })
  }

  return { position, parent, tag }
}

async function main() {
  const admin = await adminToken()
  const seed = await createDemoData(admin)

  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  })
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
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
    localStorage.setItem('user_info', JSON.stringify({ id: 1, role: 'admin', display_name: 'Base Data Admin' }))
  }, admin)

  await page.goto(`${APP}/#/admin`)
  await page.getByText('标准职位库').click()
  const positionRow = page.getByRole('row', { name: new RegExp(seed.position.name) })
  await positionRow.waitFor({ timeout: 15000 })
  await positionRow.getByText('查看详情').click({ timeout: 5000 })
  await page.getByText('标准职位详情').waitFor({ timeout: 10000 })
  await page.getByText(seed.position.name, { exact: true }).first().waitFor({ timeout: 10000 })
  await page.getByText(seed.position.aliases[0], { exact: true }).first().waitFor({ timeout: 10000 })
  await page.getByText(seed.position.description, { exact: true }).first().waitFor({ timeout: 10000 })
  await page.screenshot({ path: path.join(OUT, 'base-data-position-detail.png'), fullPage: true })

  await page.goto(`${APP}/#/admin`)
  await page.getByText('标签库').click()
  await page.waitForURL('**/#/admin/tags', { timeout: 5000 })
  const tagRow = page.getByRole('row', { name: new RegExp(seed.tag.name) })
  await tagRow.waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'base-data-tag-list.png'), fullPage: true })
  await tagRow.getByText('查看详情').click({ timeout: 5000 })
  await page.getByText('标签详情').waitFor({ timeout: 10000 })
  await page.getByText(seed.tag.name, { exact: true }).first().waitFor({ timeout: 10000 })
  await page.getByText(seed.parent.name, { exact: true }).first().waitFor({ timeout: 10000 })
  await page.getByText(seed.tag.description, { exact: true }).first().waitFor({ timeout: 10000 })
  await page.screenshot({ path: path.join(OUT, 'base-data-tag-detail.png'), fullPage: true })

  await browser.close()
  console.log(JSON.stringify({
    ok: true,
    position_id: seed.position.id,
    tag_id: seed.tag.id,
    screenshots: ['base-data-position-detail.png', 'base-data-tag-list.png', 'base-data-tag-detail.png'],
  }))
}

main().catch(error => {
  console.error(error)
  process.exit(1)
})
