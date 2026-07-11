const fs = require('fs')
const path = require('path')

const root = path.resolve(__dirname, '../..')
const src = path.join(root, 'src')
const appPath = path.join(src, 'admin-ra/app/AdminRaApp.jsx')
const dataProviderPath = path.join(src, 'admin-ra/app/dataProvider.js')
const strategyDir = path.join(src, 'admin-ra/resources/intelligent-strategies')

function fail(message) {
  console.error(message)
  process.exit(1)
}

function read(file) {
  if (!fs.existsSync(file)) {
    fail(`Missing required file: ${path.relative(root, file)}`)
  }
  return fs.readFileSync(file, 'utf8')
}

const app = read(appPath)
const dataProvider = read(dataProviderPath)

const requiredDataProviderSnippets = [
  "'intelligent-strategies': '/api/v1/matches/intelligent/strategies'",
  'cloneIntelligentStrategy',
  'runIntelligentEvaluation',
  'getIntelligentEvaluation',
  'toIntelligentStrategyPayload',
  'hybrid_weights_total_must_equal_1',
]

for (const snippet of requiredDataProviderSnippets) {
  if (!dataProvider.includes(snippet)) {
    fail(`dataProvider missing P4 intelligent snippet: ${snippet}`)
  }
}

const requiredAppSnippets = [
  'IntelligentIcon',
  'Intelligent Matching',
  '/admin-ra/intelligent-matching/strategies',
  'IntelligentStrategyList',
  'IntelligentStrategyForm',
  'IntelligentStrategyShow',
]

for (const snippet of requiredAppSnippets) {
  if (!app.includes(snippet)) {
    fail(`AdminRaApp missing P4 intelligent snippet: ${snippet}`)
  }
}

const requiredFiles = [
  'list.jsx',
  'show.jsx',
  'form.jsx',
]

for (const file of requiredFiles) {
  read(path.join(strategyDir, file))
}

const list = read(path.join(strategyDir, 'list.jsx'))
const show = read(path.join(strategyDir, 'show.jsx'))
const form = read(path.join(strategyDir, 'form.jsx'))

const requiredPageSnippets = [
  [list, 'Create Draft'],
  [list, 'vector_recall_enabled'],
  [list, 'Clone'],
  [list, 'Run Evaluation'],
  [show, 'Decision status'],
  [show, 'sample_source_distribution'],
  [show, 'Non-launch evidence'],
  [form, 'behavior_quality_score'],
  [form, 'readOnly'],
  [form, 'Clone into Draft'],
  [form, 'base_rule_config_id'],
]

for (const [content, snippet] of requiredPageSnippets) {
  if (!content.includes(snippet)) {
    fail(`P4 intelligent page missing snippet: ${snippet}`)
  }
}

console.log(JSON.stringify({
  ok: true,
  resource: 'intelligent-strategies',
  routes: [
    '/admin-ra/intelligent-matching/strategies',
    '/admin-ra/intelligent-matching/strategies/:id',
    '/admin-ra/intelligent-matching/strategies/:id/edit',
  ],
}))
