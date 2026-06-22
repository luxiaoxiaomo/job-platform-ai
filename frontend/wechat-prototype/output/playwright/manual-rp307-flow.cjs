const path = require('path')
const { deflateRawSync } = require('zlib')

let chromium
try {
  chromium = require('playwright').chromium
} catch {
  chromium = require('D:/tmp/pwmanual/node_modules/playwright').chromium
}

const API = 'http://127.0.0.1:8003'
const APP = 'http://127.0.0.1:5174'
const OUT = 'D:/AIposition/frontend/wechat-prototype/output/playwright'

function crc32(buffer) {
  let crc = 0xffffffff
  for (let index = 0; index < buffer.length; index += 1) {
    crc ^= buffer[index]
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1))
    }
  }
  return (crc ^ 0xffffffff) >>> 0
}

function zip(files) {
  const localParts = []
  const centralParts = []
  let offset = 0
  for (const file of files) {
    const name = Buffer.from(file.name)
    const data = Buffer.from(file.data)
    const compressed = deflateRawSync(data)
    const crc = crc32(data)
    const local = Buffer.alloc(30 + name.length)
    local.writeUInt32LE(0x04034b50, 0)
    local.writeUInt16LE(20, 4)
    local.writeUInt16LE(0, 6)
    local.writeUInt16LE(8, 8)
    local.writeUInt32LE(0, 10)
    local.writeUInt32LE(crc, 14)
    local.writeUInt32LE(compressed.length, 18)
    local.writeUInt32LE(data.length, 22)
    local.writeUInt16LE(name.length, 26)
    name.copy(local, 30)
    localParts.push(local, compressed)

    const central = Buffer.alloc(46 + name.length)
    central.writeUInt32LE(0x02014b50, 0)
    central.writeUInt16LE(20, 4)
    central.writeUInt16LE(20, 6)
    central.writeUInt16LE(0, 8)
    central.writeUInt16LE(8, 10)
    central.writeUInt32LE(0, 12)
    central.writeUInt32LE(crc, 16)
    central.writeUInt32LE(compressed.length, 20)
    central.writeUInt32LE(data.length, 24)
    central.writeUInt16LE(name.length, 28)
    central.writeUInt32LE(offset, 42)
    name.copy(central, 46)
    centralParts.push(central)
    offset += local.length + compressed.length
  }
  const centralOffset = offset
  const central = Buffer.concat(centralParts)
  const end = Buffer.alloc(22)
  end.writeUInt32LE(0x06054b50, 0)
  end.writeUInt16LE(files.length, 8)
  end.writeUInt16LE(files.length, 10)
  end.writeUInt32LE(central.length, 12)
  end.writeUInt32LE(centralOffset, 16)
  return Buffer.concat([...localParts, central, end])
}

function docxBytes(text) {
  const documentXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>${text}</w:t></w:r></w:p>
  </w:body>
</w:document>`
  return zip([
    { name: '[Content_Types].xml', data: '<?xml version="1.0"?><Types/>' },
    { name: 'word/document.xml', data: documentXml },
  ])
}

async function api(apiPath, options = {}) {
  const response = await fetch(`${API}${apiPath}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
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

async function tokenFor(user) {
  try {
    const login = await api('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ phone: user.phone, password: user.password }),
    })
    return login.access_token
  } catch {
    const codeResponse = await api(`/api/v1/auth/send-verification-code?phone=${encodeURIComponent(user.phone)}`, {
      method: 'POST',
    })
    const registered = await api('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ ...user, verification_code: codeResponse.code }),
    })
    return registered.access_token
  }
}

async function adminToken() {
  const login = await api('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ phone: '13700137001', password: 'Admin1234' }),
  })
  return login.access_token
}

async function ensureCertifiedRecruiter(recruiterToken, admin) {
  const status = await api('/api/v1/company-certifications/me', {
    headers: { Authorization: `Bearer ${recruiterToken}` },
  })
  if (status.status === 'approved') {
    return
  }
  if (status.status === 'not_submitted') {
    await api('/api/v1/company-certifications/me', {
      method: 'POST',
      headers: { Authorization: `Bearer ${recruiterToken}` },
      body: JSON.stringify({
        company_name: 'RP307 Test Company',
        unified_social_credit_code: `91330100MA2${Date.now().toString().slice(-7)}`,
        legal_representative: 'Tester',
        registered_address: 'Hangzhou Test Road 100',
        license_file_url: 'mock://licenses/rp307.pdf',
        license_file_name: 'rp307.pdf',
      }),
    })
  }
  const pending = await api('/api/v1/company-certifications/admin?status=pending', {
    headers: { Authorization: `Bearer ${admin}` },
  })
  const item = pending.items.find(entry => entry.company_name === 'RP307 Test Company') || pending.items[0]
  if (item) {
    await api(`/api/v1/company-certifications/admin/${item.id}/review`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${admin}` },
      body: JSON.stringify({ action: 'approve' }),
    })
  }
}

async function createActiveJob(recruiterToken, admin) {
  const job = await api('/api/v1/jobs/me', {
    method: 'POST',
    headers: { Authorization: `Bearer ${recruiterToken}` },
    body: JSON.stringify({
      title: `R-P3-07 PeopleSoft ${Date.now()}`,
      city: '上海',
      salary_min: 18,
      salary_max: 28,
      experience: '3年以上',
      education: '本科',
      description: '负责 PeopleSoft HCM 实施、二次开发和上线支持。',
      requirement: '熟悉 PeopleSoft HCM、Oracle、SQL，有企业级项目交付经验。',
      benefits: '五险一金、双休',
      tags: ['PeopleSoft', 'HCM', 'Oracle', 'SQL'],
    }),
  })
  await api(`/api/v1/jobs/admin/${job.id}/review`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${admin}` },
    body: JSON.stringify({ action: 'approve' }),
  })
  return job.id
}

async function ensureStructuredResume(seekerToken) {
  const resumeText = '姓名：RP307\nPeopleSoft HCM SQL\n本科\n4年经验\n上海\n期望薪资20-25K'
  const form = new FormData()
  form.append('file', new Blob([docxBytes(resumeText)], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }), 'rp307.docx')
  const uploaded = await api('/api/v1/resumes/me/upload', {
    method: 'POST',
    headers: { Authorization: `Bearer ${seekerToken}` },
    body: form,
  })
  await api('/api/v1/resumes/me/structured/confirm', {
    method: 'PUT',
    headers: { Authorization: `Bearer ${seekerToken}` },
    body: JSON.stringify({
      parse_run_id: uploaded.parse_run.id,
      min_confidence: 0,
      structured_json: {
        basic: {
          name: 'RP307',
          gender: '男',
          highest_education: '本科',
          work_years: 4,
          current_city: '上海',
          target_position: 'PeopleSoft 技术顾问',
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

async function createTreatmentRule(admin, source) {
  const response = await api(`/api/v1/matches/rule-configs/${source.id}/versions`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${admin}` },
    body: JSON.stringify({
      name: `R-P3-07 Browser Treatment ${Date.now()}`,
      description: 'Browser acceptance treatment rule',
      status: 'testing',
      scope: source.scope,
      template_key: source.template_key,
      template_name: source.template_name,
      dimensions: source.dimensions.map(item => ({
        key: item.key,
        label: item.label,
        weight: item.key === 'skill' ? 50 : Number(item.configured_weight),
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
  const suffix = Date.now().toString().slice(-8)
  const admin = await adminToken()
  const recruiterToken = await tokenFor({
    phone: `139${suffix}`,
    password: 'Recruiter123',
    display_name: 'RP307 Recruiter',
    role: 'recruiter',
  })
  const seekerToken = await tokenFor({
    phone: `138${suffix}`,
    password: 'Test1234',
    display_name: 'RP307 Seeker',
    role: 'seeker',
  })

  await ensureCertifiedRecruiter(recruiterToken, admin)
  const jobId = await createActiveJob(recruiterToken, admin)
  await ensureStructuredResume(seekerToken)

  const rules = await api('/api/v1/matches/rule-configs', {
    headers: { Authorization: `Bearer ${admin}` },
  })
  const source = rules.items.find(rule => rule.scope === 'global' && rule.template_key === 'default' && rule.status === 'active') || rules.items[0]
  const treatment = await createTreatmentRule(admin, source)
  const experiment = await api('/api/v1/matches/rule-experiments', {
    method: 'POST',
    headers: { Authorization: `Bearer ${admin}` },
    body: JSON.stringify({
      name: `R-P3-07 Browser AB ${Date.now()}`,
      description: 'Browser acceptance running experiment',
      scope: 'global',
      template_key: 'default',
      status: 'running',
      traffic_percent: 100,
      control_config_id: Number(source.id),
      treatment_config_id: Number(treatment.id),
      audience: {},
    }),
  })

  const match = await api(`/api/v1/matches/jobs/${jobId}/me`, {
    headers: { Authorization: `Bearer ${seekerToken}` },
  })
  if (match.source.experiment_id !== experiment.id || match.source.experiment_bucket !== 'treatment') {
    throw new Error(`Experiment did not route to treatment: ${JSON.stringify(match.source)}`)
  }
  const audits = await api(`/api/v1/matches/audits?experiment_id=${experiment.id}`, {
    headers: { Authorization: `Bearer ${admin}` },
  })
  const effects = await api(`/api/v1/matches/rule-experiments/${experiment.id}/effects`, {
    headers: { Authorization: `Bearer ${admin}` },
  })
  if (!audits.total || !effects.buckets.treatment.match_count) {
    throw new Error(`Audit/effect query failed: audits=${audits.total}, effects=${JSON.stringify(effects)}`)
  }

  const browser = await chromium.launch({ headless: false })
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
  await page.goto(APP)
  await page.evaluate((accessToken) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('user_info', JSON.stringify({ role: 'admin', display_name: 'R-P3-07 Admin' }))
  }, admin)

  await page.goto(`${APP}/#/admin-ra/rule-experiments`)
  await page.getByText('Gray / AB Test Entry').waitFor({ timeout: 15000 })
  await page.getByText(experiment.name).waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp307-experiment-list.png'), fullPage: true })

  const row = page.getByRole('row').filter({ hasText: experiment.name })
  await row.getByRole('button', { name: /View Effects/i }).click()
  await page.getByText(`Effects and match audit trail for experiment #${experiment.id}`).waitFor({ timeout: 15000 })
  await page.getByText('Recent Match Audits').waitFor({ timeout: 15000 })
  await page.getByText('treatment').first().waitFor({ timeout: 15000 })
  await page.screenshot({ path: path.join(OUT, 'rp307-effects-audits.png'), fullPage: true })

  await browser.close()
  console.log(JSON.stringify({
    ok: true,
    jobId,
    experimentId: experiment.id,
    matchSource: match.source,
    auditTotal: audits.total,
    treatmentCount: effects.buckets.treatment.match_count,
  }))
}

main().catch(error => {
  console.error(error)
  process.exit(1)
})
