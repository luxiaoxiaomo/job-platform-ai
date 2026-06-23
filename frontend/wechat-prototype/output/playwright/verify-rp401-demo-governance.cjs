const fs = require('fs')
const path = require('path')

const root = path.resolve(__dirname, '../../..')
const repoRoot = path.resolve(root, '..')
const seedPath = path.join(repoRoot, 'backend/job-platform/scripts/seed_rp401_demo.py')
const acceptancePath = path.join(__dirname, 'manual-rp401-demo-acceptance.cjs')
const seedManifestPath = path.join(__dirname, 'rp401-demo-seed.json')

function fail(message) {
  console.error(message)
  process.exit(1)
}

for (const file of [seedPath, acceptancePath]) {
  if (!fs.existsSync(file)) {
    fail(`Missing required RP401 artifact: ${file}`)
  }
}

const seed = fs.readFileSync(seedPath, 'utf8')
const acceptance = fs.readFileSync(acceptancePath, 'utf8')

const seedSnippets = [
  'RP401_DEMO_BOUNDARY',
  'MATCH_QUALITY_ONLY',
  'LOCAL_DEMO_ONLY',
  'NOT_PRODUCTION_CREDENTIALS',
  'NOT_FULL_BUSINESS_LOOP_EVIDENCE',
  'assert_demo_environment',
  'APP_ENV',
  'ENVIRONMENT',
  'production',
]

const acceptanceSnippets = [
  'RP401_DEMO_BOUNDARY',
  'MATCH_QUALITY_ONLY',
  'LOCAL_DEMO_ONLY',
  'NOT_FULL_BUSINESS_LOOP_EVIDENCE',
  'demo_boundary',
  'not_full_business_loop_evidence',
]

for (const snippet of seedSnippets) {
  if (!seed.includes(snippet)) {
    fail(`Seed script missing governance snippet: ${snippet}`)
  }
}

if (fs.existsSync(seedManifestPath)) {
  const seedManifest = JSON.parse(fs.readFileSync(seedManifestPath, 'utf8').replace(/^\\uFEFF/, ''))
  if (seedManifest.demo_boundary?.scope !== 'MATCH_QUALITY_ONLY') {
    fail('Seed manifest missing demo_boundary.scope MATCH_QUALITY_ONLY')
  }
  if (seedManifest.demo_boundary?.credential_scope !== 'LOCAL_DEMO_ONLY') {
    fail('Seed manifest missing demo_boundary.credential_scope LOCAL_DEMO_ONLY')
  }
  if (seedManifest.demo_boundary?.launch_evidence !== 'NOT_FULL_BUSINESS_LOOP_EVIDENCE') {
    fail('Seed manifest missing demo_boundary.launch_evidence NOT_FULL_BUSINESS_LOOP_EVIDENCE')
  }
}

for (const snippet of acceptanceSnippets) {
  if (!acceptance.includes(snippet)) {
    fail(`Acceptance script missing governance snippet: ${snippet}`)
  }
}

console.log(JSON.stringify({
  ok: true,
  seed: path.basename(seedPath),
  acceptance: path.basename(acceptancePath),
  governance: 'rp401-demo-boundary-and-credential-scope',
  seed_manifest_checked: fs.existsSync(seedManifestPath),
}))
