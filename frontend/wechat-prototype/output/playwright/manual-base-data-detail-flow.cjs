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
  await page.getByRole('button', { name: '新增标准职位' }).waitFor({ timeout: 5000 })
  if (await page.getByPlaceholder('标准名称').count() !== 0) {
    throw new Error('标准职位列表仍显示旧内嵌表单')
  }

  await page.getByRole('button', { name: '新增标准职位' }).click()
  let positionDrawer = page.getByRole('dialog', { name: '新增标准职位' })
  await positionDrawer.waitFor({ timeout: 5000 })
  await positionDrawer.getByPlaceholder('例如：Java 开发工程师').fill('未保存职位')
  let confirmMessage = ''
  page.once('dialog', async dialog => {
    confirmMessage = dialog.message()
    await dialog.dismiss()
  })
  await positionDrawer.getByRole('button', { name: '关闭抽屉' }).click()
  await positionDrawer.waitFor({ state: 'visible' })
  if (!confirmMessage.includes('尚未保存')) throw new Error(`缺少脏数据确认: ${confirmMessage}`)
  page.once('dialog', dialog => dialog.accept())
  await positionDrawer.getByRole('button', { name: '关闭抽屉' }).click()
  await positionDrawer.waitFor({ state: 'hidden' })

  const suffix = Date.now().toString().slice(-7)
  const drawerPositionName = `BD Drawer Position ${suffix}`
  const drawerPositionDescription = `Drawer position created ${suffix}`
  const drawerPositionUpdatedDescription = `Drawer position updated ${suffix}`
  await page.getByRole('button', { name: '新增标准职位' }).click()
  positionDrawer = page.getByRole('dialog', { name: '新增标准职位' })
  await positionDrawer.getByPlaceholder('例如：Java 开发工程师').fill(drawerPositionName)
  await positionDrawer.getByPlaceholder('例如：技术 / 研发').fill('Drawer QA')
  await positionDrawer.getByPlaceholder('多个别名使用逗号分隔').fill(`Drawer Alias ${suffix}, QA Alias ${suffix}`)
  await positionDrawer.getByPlaceholder('补充职位边界或使用说明').fill(drawerPositionDescription)
  await positionDrawer.getByRole('button', { name: '创建标准职位' }).click()
  await positionDrawer.waitFor({ state: 'hidden', timeout: 10000 })

  let drawerPositionRow = page.getByRole('row', { name: new RegExp(drawerPositionName) })
  await drawerPositionRow.waitFor({ timeout: 10000 })
  await drawerPositionRow.getByText('编辑').click()
  const positionEditDrawer = page.getByRole('dialog', { name: '编辑标准职位' })
  const positionNameInput = positionEditDrawer.getByPlaceholder('例如：Java 开发工程师')
  await positionNameInput.waitFor({ timeout: 10000 })
  if (await positionNameInput.inputValue() !== drawerPositionName) throw new Error('标准职位编辑抽屉未加载最新详情')
  await positionEditDrawer.getByPlaceholder('补充职位边界或使用说明').fill(drawerPositionUpdatedDescription)
  await positionEditDrawer.getByRole('button', { name: '保存修改' }).click()
  await positionEditDrawer.waitFor({ state: 'hidden', timeout: 10000 })

  drawerPositionRow = page.getByRole('row', { name: new RegExp(drawerPositionName) })
  await drawerPositionRow.getByText('查看详情').click()
  await page.getByText('标准职位详情').waitFor({ timeout: 10000 })
  await page.getByText(drawerPositionName, { exact: true }).first().waitFor({ timeout: 10000 })
  await page.getByText(drawerPositionUpdatedDescription, { exact: true }).first().waitFor({ timeout: 10000 })
  await page.screenshot({ path: path.join(OUT, 'base-data-position-detail.png'), fullPage: true })

  await page.goto(`${APP}/#/admin`)
  await page.getByText('标签库').click()
  await page.waitForURL('**/#/admin/tags', { timeout: 5000 })
  await page.getByRole('button', { name: '新增标签' }).waitFor({ timeout: 5000 })
  if (await page.getByPlaceholder('标签名称').count() !== 0) {
    throw new Error('标签列表仍显示旧内嵌表单')
  }

  const drawerTagName = `BD Drawer Tag ${suffix}`
  const drawerTagDescription = `Drawer tag created ${suffix}`
  const drawerTagUpdatedDescription = `Drawer tag updated ${suffix}`
  await page.getByRole('button', { name: '新增标签' }).click()
  const tagDrawer = page.getByRole('dialog', { name: '新增标签' })
  await tagDrawer.getByPlaceholder('例如：PeopleSoft').fill(drawerTagName)
  await tagDrawer.getByPlaceholder('例如：skill / industry').fill('skill-detail')
  await tagDrawer.getByLabel('父级标签').selectOption(String(seed.parent.id))
  await tagDrawer.getByPlaceholder('#2563eb').fill('#7c3aed')
  await tagDrawer.getByLabel('排序').fill('21')
  await tagDrawer.getByPlaceholder('补充标签含义或使用范围').fill(drawerTagDescription)
  await tagDrawer.getByRole('button', { name: '创建标签' }).click()
  await tagDrawer.waitFor({ state: 'hidden', timeout: 10000 })

  let drawerTagRow = page.getByRole('row', { name: new RegExp(drawerTagName) })
  await drawerTagRow.waitFor({ timeout: 10000 })
  await drawerTagRow.getByText('编辑').click()
  const tagEditDrawer = page.getByRole('dialog', { name: '编辑标签' })
  const tagNameInput = tagEditDrawer.getByPlaceholder('例如：PeopleSoft')
  await tagNameInput.waitFor({ timeout: 10000 })
  if (await tagNameInput.inputValue() !== drawerTagName) throw new Error('标签编辑抽屉未加载最新详情')
  if (await tagEditDrawer.getByLabel('父级标签').locator(`option:has-text("${drawerTagName}")`).count() !== 0) {
    throw new Error('标签编辑抽屉允许选择自身作为父级')
  }
  await tagEditDrawer.getByPlaceholder('补充标签含义或使用范围').fill(drawerTagUpdatedDescription)
  await tagEditDrawer.getByRole('button', { name: '保存修改' }).click()
  await tagEditDrawer.waitFor({ state: 'hidden', timeout: 10000 })

  drawerTagRow = page.getByRole('row', { name: new RegExp(drawerTagName) })
  await page.screenshot({ path: path.join(OUT, 'base-data-tag-list.png'), fullPage: true })
  await drawerTagRow.getByText('查看详情').click({ timeout: 5000 })
  await page.getByText('标签详情').waitFor({ timeout: 10000 })
  await page.getByText(drawerTagName, { exact: true }).first().waitFor({ timeout: 10000 })
  await page.getByText(seed.parent.name, { exact: true }).first().waitFor({ timeout: 10000 })
  await page.getByText(drawerTagUpdatedDescription, { exact: true }).first().waitFor({ timeout: 10000 })
  await page.screenshot({ path: path.join(OUT, 'base-data-tag-detail.png'), fullPage: true })

  await browser.close()
  console.log(JSON.stringify({
    ok: true,
    seed_position_id: seed.position.id,
    seed_tag_id: seed.tag.id,
    drawer_position: drawerPositionName,
    drawer_tag: drawerTagName,
    screenshots: ['base-data-position-detail.png', 'base-data-tag-list.png', 'base-data-tag-detail.png'],
  }))
}

main().catch(error => {
  console.error(error)
  process.exit(1)
})
