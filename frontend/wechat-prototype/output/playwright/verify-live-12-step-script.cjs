const fs = require('fs')
const path = require('path')

const target = path.join(__dirname, 'manual-live-12-step-e2e.cjs')

function fail(message) {
  console.error(message)
  process.exit(1)
}

if (!fs.existsSync(target)) {
  fail(`Missing live 12-step script: ${target}`)
}

const source = fs.readFileSync(target, 'utf8')
const requiredSnippets = [
  'manual-live-12-step-e2e-manifest',
  'evidence_type',
  'real API-backed',
  'mock-only',
  'failOnMockOnly',
  '/api/v1/company-certifications/me',
  '/api/v1/jobs/me',
  '/api/v1/jobs/admin',
  '/api/v1/jobs/public',
  '/api/v1/resumes/me/upload',
  '/api/v1/matches/jobs/',
  '/api/v1/applications',
  '/api/v1/messages/conversations/open',
  '/api/v1/messages/contact-exchanges',
  '/api/v1/applications/recruiter/stats/business-loop',
  '/api/v1/matches/quality/summary',
  'seeker_contact_exchange_reread',
  'recruiter_contact_exchange_reread',
  'accepted structured contact visibility',
  'contact_exchange.status',
]

for (const snippet of requiredSnippets) {
  if (!source.includes(snippet)) {
    fail(`Missing required snippet in live script: ${snippet}`)
  }
}

const stepMatches = source.match(/recordStep\(\{/g) || []
if (stepMatches.length !== 12) {
  fail(`Expected exactly 12 recorded business steps, found ${stepMatches.length}`)
}

console.log(JSON.stringify({
  ok: true,
  script: path.basename(target),
  recorded_steps: stepMatches.length,
}))
