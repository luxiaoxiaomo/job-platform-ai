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
const RUN_ID = `live-12-step-${new Date().toISOString().replace(/[:.]/g, '-')}`
const MANIFEST_PATH = path.join(OUT, `manual-live-12-step-e2e-manifest-${RUN_ID}.json`)

const manifest = {
  run_id: RUN_ID,
  script: 'manual-live-12-step-e2e.cjs',
  started_at: new Date().toISOString(),
  completed_at: null,
  environment: 'local-demo',
  api_base_url: API,
  app_base_url: APP,
  manifest_kind: 'manual-live-12-step-e2e-manifest',
  evidence_policy: {
    accepted: ['real API-backed'],
    rejected: ['mock-only'],
    note: 'This script records only real API-backed steps as launch-candidate evidence.',
  },
  accounts: {},
  ids: {},
  steps: [],
  api_checks: [],
  screenshots: [],
  known_gaps: [],
}

function writeManifest() {
  fs.mkdirSync(OUT, { recursive: true })
  fs.writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2), 'utf8')
}

function failOnMockOnly(step) {
  if (step.evidence_type === 'mock-only') {
    throw new Error(`Step ${step.step} attempted to use mock-only evidence`)
  }
}

function requireCondition(condition, message, details) {
  if (!condition) {
    throw new Error(`${message}${details ? `: ${JSON.stringify(details)}` : ''}`)
  }
}

function recordStep(step) {
  failOnMockOnly(step)
  const entry = {
    evidence_type: 'real API-backed',
    source: 'api',
    recorded_at: new Date().toISOString(),
    ...step,
  }
  manifest.steps.push(entry)
  writeManifest()
  return entry
}

function recordApiCheck(name, result) {
  manifest.api_checks.push({ name, recorded_at: new Date().toISOString(), ...result })
  writeManifest()
}

async function api(apiPath, options = {}) {
  const response = await fetch(`${API}${apiPath}`, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
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
  const codeResponse = await api(`/api/v1/auth/send-verification-code?phone=${phone}`, { method: 'POST' })
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
  return { token: response.access_token, user: response.user || {}, phone, role, displayName }
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
  const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const documentXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>${escaped}</w:t></w:r></w:p></w:body>
</w:document>`
  return zipFile([
    { name: '[Content_Types].xml', data: '<?xml version="1.0"?><Types/>' },
    { name: 'word/document.xml', data: documentXml },
  ])
}

async function uploadAndConfirmResume(seekerToken) {
  const form = new FormData()
  form.append(
    'file',
    new Blob([buildDocx('PeopleSoft HCM SQL Bachelor 4 years Shanghai salary 20-25K')], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }),
    'live-12-step-resume.docx',
  )
  const upload = await fetch(`${API}/api/v1/resumes/me/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${seekerToken}` },
    body: form,
  })
  if (!upload.ok) {
    throw new Error(`POST /api/v1/resumes/me/upload failed ${upload.status}: ${await upload.text()}`)
  }
  const uploadJson = await upload.json()
  const resume = uploadJson.resume || {}
  const parseRunId = uploadJson.parse_run?.id
  if (parseRunId) {
    await api('/api/v1/resumes/me/structured/confirm', {
      method: 'PUT',
      headers: { Authorization: `Bearer ${seekerToken}` },
      body: JSON.stringify({
        parse_run_id: parseRunId,
        min_confidence: 0,
        structured_json: {
          basic: {
            name: 'Live Demo Seeker',
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
  return { resume, parseRunId }
}

async function captureAdminScreenshot(admin, ruleConfigId) {
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  })
  try {
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
      localStorage.setItem('user_info', JSON.stringify({ id: 1, role: 'admin', display_name: 'Live 12-step Admin' }))
    }, admin)
    await page.goto(`${APP}/#/admin-ra/match-quality`)
    const mainContent = page.locator('#main-content')
    await mainContent.getByRole('heading', { name: 'Match Quality', exact: true }).waitFor({ timeout: 15000 })
    await page.getByLabel('Rule Config ID').fill(String(ruleConfigId))
    await page.getByRole('button', { name: /Apply/i }).click()
    await page.getByText(String(ruleConfigId)).first().waitFor({ timeout: 15000 })
    const screenshot = `manual-live-12-step-match-quality-${RUN_ID}.png`
    await page.screenshot({ path: path.join(OUT, screenshot), fullPage: true })
    manifest.screenshots.push(screenshot)
    writeManifest()
  } finally {
    await browser.close()
  }
}

async function main() {
  writeManifest()
  const suffix = Date.now().toString().slice(-8)
  const admin = await adminToken()
  manifest.accounts.admin = { phone: '13700137001', source: 'local-demo-fixed' }

  const recruiter = await registerUser(`139${suffix}`, 'recruiter', `L12R${suffix}`)
  manifest.accounts.recruiter = { phone: recruiter.phone, role: recruiter.role, source: 'generated' }
  recordStep({ step: 1, name: 'recruiter_register', endpoint: '/api/v1/auth/register', result: { role: recruiter.role } })

  const certification = await api('/api/v1/company-certifications/me', {
    method: 'POST',
    headers: { Authorization: `Bearer ${recruiter.token}` },
    body: JSON.stringify({
      company_name: `Live 12 Step Company ${suffix}`,
      unified_social_credit_code: `91330100${suffix.padStart(10, '0').slice(-10)}`,
      legal_representative: 'Live Owner',
      registered_address: 'Shanghai Demo District',
      license_file_url: 'mock://licenses/live-12-step.pdf',
      license_file_name: 'live-12-step.pdf',
    }),
  })
  const pendingCerts = await api('/api/v1/company-certifications/admin?status=pending', {
    headers: { Authorization: `Bearer ${admin}` },
  })
  requireCondition((pendingCerts.items || []).some(item => item.id === certification.id), 'Certification not found in admin pending list', pendingCerts)
  const approvedCert = await api(`/api/v1/company-certifications/admin/${certification.id}/review`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${admin}` },
    body: JSON.stringify({ action: 'approve' }),
  })
  requireCondition(approvedCert.status === 'approved', 'Certification review did not approve', approvedCert)
  manifest.ids.certification_id = certification.id
  recordStep({ step: 2, name: 'company_certification_submit_and_approve', endpoint: '/api/v1/company-certifications/me', result: { certification_id: certification.id, status: approvedCert.status } })

  const job = await api('/api/v1/jobs/me', {
    method: 'POST',
    headers: { Authorization: `Bearer ${recruiter.token}` },
    body: JSON.stringify({
      title: `Live 12 Step PeopleSoft Analyst ${suffix}`,
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
  requireCondition(job.status === 'pending', 'New job should start pending', job)
  manifest.ids.job_id = job.id
  recordStep({ step: 3, name: 'recruiter_create_job', endpoint: '/api/v1/jobs/me', result: { job_id: job.id, status: job.status } })

  const adminJobs = await api('/api/v1/jobs/admin?status=pending', { headers: { Authorization: `Bearer ${admin}` } })
  requireCondition((adminJobs.items || []).some(item => item.id === job.id), 'Job not found in admin pending list', adminJobs)
  const approvedJob = await api(`/api/v1/jobs/admin/${job.id}/review`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${admin}` },
    body: JSON.stringify({ action: 'approve' }),
  })
  requireCondition(approvedJob.status === 'active', 'Job review did not activate job', approvedJob)
  recordStep({ step: 4, name: 'admin_review_job', endpoint: '/api/v1/jobs/admin/{job_id}/review', result: { job_id: job.id, status: approvedJob.status } })

  const seeker = await registerUser(`138${suffix}`, 'seeker', `L12S${suffix}`)
  manifest.accounts.seeker = { phone: seeker.phone, role: seeker.role, source: 'generated' }
  const publicJobs = await api('/api/v1/jobs/public')
  requireCondition((publicJobs.items || []).some(item => item.id === job.id), 'Active job not visible in public list', publicJobs)
  recordStep({ step: 5, name: 'seeker_public_job_list', endpoint: '/api/v1/jobs/public', result: { job_id: job.id } })

  const publicDetail = await api(`/api/v1/jobs/public/${job.id}`, { headers: { Authorization: `Bearer ${seeker.token}` } })
  requireCondition(publicDetail.id === job.id, 'Public job detail mismatch', publicDetail)
  recordStep({ step: 6, name: 'seeker_public_job_detail', endpoint: '/api/v1/jobs/public/{job_id}', result: { job_id: publicDetail.id, view_count: publicDetail.view_count } })

  const resumeInfo = await uploadAndConfirmResume(seeker.token)
  manifest.ids.resume_id = resumeInfo.resume.id
  manifest.ids.parse_run_id = resumeInfo.parseRunId
  recordStep({ step: 7, name: 'seeker_resume_upload_and_profile_confirm', endpoint: '/api/v1/resumes/me/upload', result: { resume_id: resumeInfo.resume.id, parse_run_id: resumeInfo.parseRunId } })

  const match = await api(`/api/v1/matches/jobs/${job.id}/me`, { headers: { Authorization: `Bearer ${seeker.token}` } })
  requireCondition(match.source?.audit_id, 'Match response missing audit id', match)
  manifest.ids.match_audit_id = match.source.audit_id
  manifest.ids.rule_config_id = match.source.rule_config_id
  recordStep({ step: 8, name: 'seeker_match_job', endpoint: '/api/v1/matches/jobs/{job_id}/me', result: { audit_id: match.source.audit_id, rule_config_id: match.source.rule_config_id } })

  await api(`/api/v1/jobs/seeker/favorites/${job.id}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${seeker.token}` },
  })
  const application = await api('/api/v1/applications', {
    method: 'POST',
    headers: { Authorization: `Bearer ${seeker.token}` },
    body: JSON.stringify({ job_id: job.id, cover_message: 'Live 12-step acceptance application.' }),
  })
  requireCondition(application.status === 'submitted', 'Application should be submitted', application)
  manifest.ids.application_id = application.id
  recordStep({ step: 9, name: 'seeker_favorite_and_apply', endpoint: '/api/v1/applications', result: { application_id: application.id, status: application.status } })

  const conversation = await api('/api/v1/messages/conversations/open', {
    method: 'POST',
    headers: { Authorization: `Bearer ${seeker.token}` },
    body: JSON.stringify({ job_id: job.id }),
  })
  await api(`/api/v1/messages/conversations/${conversation.id}/messages`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${seeker.token}` },
    body: JSON.stringify({ content: 'Hello, I am interested in this role.' }),
  })
  await api(`/api/v1/messages/conversations/${conversation.id}/messages`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${recruiter.token}` },
    body: JSON.stringify({ content: 'Thanks, please keep your profile updated on the platform.' }),
  })
  const recruiterConversations = await api('/api/v1/messages/conversations', { headers: { Authorization: `Bearer ${recruiter.token}` } })
  requireCondition((recruiterConversations.items || []).some(item => item.id === conversation.id), 'Recruiter cannot list conversation', recruiterConversations)
  manifest.ids.conversation_id = conversation.id
  recordStep({ step: 10, name: 'conversation_open_and_reply', endpoint: '/api/v1/messages/conversations/open', result: { conversation_id: conversation.id } })

  const exchange = await api('/api/v1/messages/contact-exchanges', {
    method: 'POST',
    headers: { Authorization: `Bearer ${seeker.token}` },
    body: JSON.stringify({ conversation_id: conversation.id }),
  })
  requireCondition(exchange.status === 'pending', 'Contact exchange should start pending', exchange)
  const acceptedExchange = await api(`/api/v1/messages/contact-exchanges/${exchange.id}/review`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${recruiter.token}` },
    body: JSON.stringify({ action: 'accept' }),
  })
  requireCondition(acceptedExchange.status === 'accepted', 'Contact exchange not accepted', acceptedExchange)
  const acceptedRoles = new Set((acceptedExchange.contacts || []).map(item => item.role))
  requireCondition(acceptedRoles.has('seeker') && acceptedRoles.has('recruiter'), 'Accepted exchange missing structured contacts', acceptedExchange)

  const seekerContactReread = await api(`/api/v1/messages/conversations/${conversation.id}`, {
    headers: { Authorization: `Bearer ${seeker.token}` },
  })
  const recruiterContactReread = await api(`/api/v1/messages/conversations/${conversation.id}`, {
    headers: { Authorization: `Bearer ${recruiter.token}` },
  })
  requireCondition(
    seekerContactReread.contact_exchange?.status === 'accepted',
    'seeker_contact_exchange_reread contact_exchange.status should be accepted',
    seekerContactReread.contact_exchange,
  )
  requireCondition(
    recruiterContactReread.contact_exchange?.status === 'accepted',
    'recruiter_contact_exchange_reread contact_exchange.status should be accepted',
    recruiterContactReread.contact_exchange,
  )
  const seekerVisibleRoles = new Set((seekerContactReread.contact_exchange.contacts || []).map(item => item.role))
  const recruiterVisibleRoles = new Set((recruiterContactReread.contact_exchange.contacts || []).map(item => item.role))
  requireCondition(
    seekerVisibleRoles.has('seeker') && seekerVisibleRoles.has('recruiter'),
    'seeker accepted structured contact visibility missing both roles',
    seekerContactReread.contact_exchange,
  )
  requireCondition(
    recruiterVisibleRoles.has('seeker') && recruiterVisibleRoles.has('recruiter'),
    'recruiter accepted structured contact visibility missing both roles',
    recruiterContactReread.contact_exchange,
  )
  recordApiCheck('seeker_contact_exchange_reread', {
    endpoint: '/api/v1/messages/conversations/{conversation_id}',
    contact_exchange: {
      id: seekerContactReread.contact_exchange.id,
      status: seekerContactReread.contact_exchange.status,
      visible_contact_roles: [...seekerVisibleRoles],
    },
  })
  recordApiCheck('recruiter_contact_exchange_reread', {
    endpoint: '/api/v1/messages/conversations/{conversation_id}',
    contact_exchange: {
      id: recruiterContactReread.contact_exchange.id,
      status: recruiterContactReread.contact_exchange.status,
      visible_contact_roles: [...recruiterVisibleRoles],
    },
  })

  manifest.ids.contact_exchange_id = exchange.id
  recordStep({ step: 11, name: 'structured_contact_exchange_accept', endpoint: '/api/v1/messages/contact-exchanges', result: { exchange_id: exchange.id, status: acceptedExchange.status, contact_visibility: 'accepted structured contact visibility', contacts: acceptedExchange.contacts?.map(item => item.role) } })

  const recruiterLoop = await api('/api/v1/applications/recruiter/stats/business-loop', { headers: { Authorization: `Bearer ${recruiter.token}` } })
  const adminLoop = await api('/api/v1/applications/admin/stats/business-loop', { headers: { Authorization: `Bearer ${admin}` } })
  const quality = await api(`/api/v1/matches/quality/summary?rule_config_id=${match.source.rule_config_id}`, { headers: { Authorization: `Bearer ${admin}` } })
  requireCondition(recruiterLoop.successful_connection_count >= 1, 'Recruiter loop missing successful connection', recruiterLoop)
  requireCondition(adminLoop.successful_connection_count >= 1, 'Admin loop missing successful connection', adminLoop)
  requireCondition(quality.summary.match_count >= 1, 'Match Quality summary missing match evidence', quality.summary)
  recordApiCheck('business_loop_recruiter', { endpoint: '/api/v1/applications/recruiter/stats/business-loop', summary: recruiterLoop })
  recordApiCheck('business_loop_admin', { endpoint: '/api/v1/applications/admin/stats/business-loop', summary: adminLoop })
  recordApiCheck('match_quality_summary', { endpoint: '/api/v1/matches/quality/summary', summary: quality.summary })
  recordStep({ step: 12, name: 'business_loop_and_match_quality_reread', endpoint: '/api/v1/applications/recruiter/stats/business-loop', result: { successful_connection_count: recruiterLoop.successful_connection_count, match_count: quality.summary.match_count } })

  try {
    await captureAdminScreenshot(admin, match.source.rule_config_id)
  } catch (error) {
    manifest.known_gaps.push({ type: 'screenshot_optional_failed', message: error.message })
    writeManifest()
  }

  manifest.completed_at = new Date().toISOString()
  writeManifest()
  console.log(JSON.stringify({
    ok: true,
    manifest: MANIFEST_PATH,
    steps: manifest.steps.length,
    ids: manifest.ids,
    screenshots: manifest.screenshots,
  }))
}

main().catch(error => {
  manifest.completed_at = new Date().toISOString()
  manifest.error = error.message
  writeManifest()
  console.error(error)
  process.exit(1)
})
