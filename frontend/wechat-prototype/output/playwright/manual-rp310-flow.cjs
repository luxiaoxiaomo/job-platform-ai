const path = require('path')

let chromium
try {
  chromium = require('playwright').chromium
} catch {
  chromium = require('D:/tmp/pwmanual/node_modules/playwright').chromium
}

const API = 'http://127.0.0.1:8004'
const APP = 'http://127.0.0.1:5175'
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

async function registerUser(phone, role, displayName) {
  const codeResponse = await api(`/api/v1/auth/send-verification-code?phone=${phone}`, {
    method: 'POST',
  })
  const response = await api('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      phone,
      password: role === 'recruiter' ? 'Recruiter123' : 'Test1234',
      display_name: displayName,
      role,
      verification_code: codeResponse.code,
    }),
  })
  return response.access_token
}

async function createActiveJob(admin, recruiterToken) {
  await api('/api/v1/company-certifications/me', {
    method: 'POST',
    headers: { Authorization: `Bearer ${recruiterToken}` },
    body: JSON.stringify({
      company_name: 'RP310 Quality Company',
      unified_social_credit_code: `91330100${Date.now().toString().slice(-10)}`,
      legal_representative: 'Quality Owner',
      registered_address: 'Shanghai',
      license_file_url: 'mock://licenses/rp310.pdf',
      license_file_name: 'rp310.pdf',
    }),
  })
  const pending = await api('/api/v1/company-certifications/admin?status=pending', {
    headers: { Authorization: `Bearer ${admin}` },
  })
  const certification = (pending.items || [])[0]
  if (!certification) {
    throw new Error('No pending certification found')
  }
  await api(`/api/v1/company-certifications/admin/${certification.id}/review`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${admin}` },
    body: JSON.stringify({ action: 'approve' }),
  })

  const create = await api('/api/v1/jobs/me', {
    method: 'POST',
    headers: { Authorization: `Bearer ${recruiterToken}` },
    body: JSON.stringify({
      title: 'PeopleSoft Quality Analyst',
      city: 'Shanghai',
      salary_min: 18,
      salary_max: 28,
      experience: '3 years',
      education: 'Bachelor',
      description: 'Implement PeopleSoft HCM and support HR system delivery.',
      requirement: 'PeopleSoft HCM Oracle SQL delivery experience.',
      benefits: 'Insurance and bonus',
      tags: ['PeopleSoft', 'HCM', 'Oracle', 'SQL'],
    }),
  })
  const reviewed = await api(`/api/v1/jobs/admin/${create.id}/review`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${admin}` },
    body: JSON.stringify({ action: 'approve' }),
  })
  return reviewed.id
}

function crc32(bytes) {
  let crc = 0xffffffff
  for (const byte of bytes) {
    crc ^= byte
    for (let i = 0; i < 8; i += 1) {
      crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0)
    }
  }
  return (crc ^ 0xffffffff) >>> 0
}

function u16(value) {
  const buffer = Buffer.alloc(2)
  buffer.writeUInt16LE(value)
  return buffer
}

function u32(value) {
  const buffer = Buffer.alloc(4)
  buffer.writeUInt32LE(value)
  return buffer
}

function zipFile(entries) {
  const localParts = []
  const centralParts = []
  let offset = 0

  for (const entry of entries) {
    const name = Buffer.from(entry.name)
    const data = Buffer.from(entry.data)
    const checksum = crc32(data)
    const local = Buffer.concat([
      u32(0x04034b50), u16(20), u16(0), u16(0), u16(0), u16(0),
      u32(checksum), u32(data.length), u32(data.length), u16(name.length), u16(0), name, data,
    ])
    const central = Buffer.concat([
      u32(0x02014b50), u16(20), u16(20), u16(0), u16(0), u16(0), u16(0),
      u32(checksum), u32(data.length), u32(data.length), u16(name.length), u16(0), u16(0),
      u16(0), u16(0), u32(0), u32(offset), name,
    ])
    localParts.push(local)
    centralParts.push(central)
    offset += local.length
  }

  const central = Buffer.concat(centralParts)
  const end = Buffer.concat([
    u32(0x06054b50), u16(0), u16(0), u16(entries.length), u16(entries.length),
    u32(central.length), u32(offset), u16(0),
  ])
  return Buffer.concat([...localParts, central, end])
}

function buildDocx(text) {
  const documentXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>${text}</w:t></w:r></w:p>
  </w:body>
</w:document>`
  return zipFile([
    { name: '[Content_Types].xml', data: '<?xml version="1.0"?><Types/>' },
    { name: 'word/document.xml', data: documentXml },
  ])
}

async function confirmResume(seekerToken) {
  const form = new FormData()
  form.append(
    'file',
    new Blob([buildDocx('PeopleSoft HCM SQL Bachelor 4 years Shanghai salary 20-25K')], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }),
    'resume.docx',
  )
  const upload = await fetch(`${API}/api/v1/resumes/me/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${seekerToken}` },
    body: form,
  })
  if (!upload.ok) {
    throw new Error(`resume upload failed ${upload.status}: ${await upload.text()}`)
  }
  const uploadJson = await upload.json()
  const parseRunId = uploadJson.parse_run.id
  await api('/api/v1/resumes/me/structured/confirm', {
    method: 'PUT',
    headers: { Authorization: `Bearer ${seekerToken}` },
    body: JSON.stringify({
      parse_run_id: parseRunId,
      min_confidence: 0,
      structured_json: {
        basic: {
          name: 'Quality Seeker',
          gender: 'male',
          highest_education: 'Bachelor',
          work_years: 4,
          current_city: 'Shanghai',
          target_position: 'PeopleSoft Quality Analyst',
          expected_salary: '20-25K',
          confidence_score: 0.95,
        },
        skills: [
          { skill_name: 'PeopleSoft', confidence_score: 0.95 },
          { skill_name: 'HCM', confidence_score: 0.9 },
          { skill_name: 'SQL', confidence_score: 0.9 },
        ],
      },
    }),
  })
}

async function main() {
  const suffix = Date.now()
  const admin = await adminToken()
  const recruiter = await registerUser(`139${String(suffix).slice(-8)}`, 'recruiter', `RP310R${String(suffix).slice(-6)}`)
  const seeker = await registerUser(`138${String(suffix).slice(-8)}`, 'seeker', `RP310S${String(suffix).slice(-6)}`)
  const jobId = await createActiveJob(admin, recruiter)
  await confirmResume(seeker)

  await api(`/api/v1/jobs/public/${jobId}`, {
    headers: { Authorization: `Bearer ${seeker}` },
  })
  const match = await api(`/api/v1/matches/jobs/${jobId}/me`, {
    headers: { Authorization: `Bearer ${seeker}` },
  })
  await api(`/api/v1/jobs/seeker/favorites/${jobId}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${seeker}` },
  })
  await api('/api/v1/applications', {
    method: 'POST',
    headers: { Authorization: `Bearer ${seeker}` },
    body: JSON.stringify({ job_id: jobId, cover_message: 'R-P3-10 browser acceptance' }),
  })

  const quality = await api(`/api/v1/matches/quality/summary?rule_config_id=${match.source.rule_config_id}`, {
    headers: { Authorization: `Bearer ${admin}` },
  })
  if (quality.summary.match_count < 1 || quality.summary.application_count < 1 || quality.summary.favorite_count < 1 || quality.summary.visit_count < 1) {
    throw new Error(`quality summary missing downstream metrics: ${JSON.stringify(quality.summary)}`)
  }

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
    localStorage.setItem('user_info', JSON.stringify({ id: 1, role: 'admin', display_name: 'R-P3-10 Admin' }))
  }, admin)

  await page.goto(`${APP}/#/admin-ra/match-quality`)
  const mainContent = page.locator('#main-content')
  await mainContent.getByRole('heading', { name: 'Match Quality', exact: true }).waitFor({ timeout: 15000 })
  await page.getByText('Rule Versions').waitFor({ timeout: 15000 })
  await page.getByText('Experiment Buckets').waitFor({ timeout: 15000 })
  await page.getByText('Daily Trend').waitFor({ timeout: 15000 })
  await page.getByText('Applications').first().waitFor({ timeout: 15000 })
  await page.getByText(String(quality.summary.application_count)).first().waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp310-quality-dashboard.png'), fullPage: true })

  const ruleInput = page.getByLabel('Rule Config ID')
  await ruleInput.fill(String(match.source.rule_config_id))
  await page.getByRole('button', { name: /Apply/i }).click()
  await page.getByText(String(match.source.rule_config_id)).first().waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp310-quality-filtered.png'), fullPage: true })

  await browser.close()
  console.log(JSON.stringify({
    ok: true,
    jobId,
    auditId: match.source.audit_id,
    ruleConfigId: match.source.rule_config_id,
    summary: quality.summary,
    screenshots: [
      'rp310-quality-dashboard.png',
      'rp310-quality-filtered.png',
    ],
  }))
}

main().catch(error => {
  console.error(error)
  process.exit(1)
})
