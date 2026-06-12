import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useToast } from '../components/ui.jsx'
import { LineChart, ScoreBar } from '../components/charts.jsx'
import { adminStats, adminReviewQueue, adminUsers, adminAIMetrics, adminJobLib } from '../mock/data.js'
import {
  createPromptConfig,
  getActivePromptConfig,
  listCompanyCertifications,
  listPromptConfigs,
  publishPromptConfig,
  reviewCompanyCertification,
  testPromptConfig,
} from '../services/index.js'
import '../styles/admin.css'

const NAV = [
  { key: 'dash', icon: '📊', label: '数据概览' },
  { key: 'review', icon: '✅', label: '审核管理' },
  { key: 'users', icon: '👥', label: '用户管理' },
  { key: 'ai', icon: '⚡', label: 'AI 监控' },
  { key: 'data', icon: '🗂', label: '基础数据' },
]

const CERT_STATUS_FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '待审核' },
  { key: 'approved', label: '已通过' },
  { key: 'rejected', label: '已驳回' },
]

const CERT_STATUS_META = {
  pending: { label: '待审核', tag: 'warn' },
  approved: { label: '已通过', tag: 'pass' },
  rejected: { label: '已驳回', tag: 'block' },
}

const CERT_METHOD_LABELS = {
  business_license: '营业执照',
  enterprise_email: '企业邮箱',
  hr_authorization: 'HR授权',
}

export function AdminApp() {
  const [page, setPage] = useState('dash')
  const navigate = useNavigate()
  const title = NAV.find(n => n.key === page).label
  return (
    <div className="admin">
      <aside className="admin-side">
        <div className="admin-brand"><span className="dot" />空岗平台 · 运营后台</div>
        <nav className="admin-nav">
          {NAV.map(n => (
            <div key={n.key} className={`nav-item ${page === n.key ? 'active' : ''}`} onClick={() => setPage(n.key)}>
              <span className="ico">{n.icon}</span>{n.label}
            </div>
          ))}
        </nav>
        <div className="admin-side-foot" onClick={() => navigate('/')}>← 返回原型首页</div>
      </aside>
      <main className="admin-main">
        <header className="admin-topbar">
          <span className="at-title">{title}</span>
          <div className="at-right"><span>🔔</span><span>管理员 · admin</span></div>
        </header>
        <div className="admin-content">
          {page === 'dash' && <Dash />}
          {page === 'review' && <Review />}
          {page === 'users' && <Users />}
          {page === 'ai' && <AIMonitor />}
          {page === 'data' && <BaseData />}
        </div>
      </main>
    </div>
  )
}

function Dash() {
  const s = adminStats
  return (
    <>
      <div className="admin-kpis">
        {s.kpis.map(k => (
          <div key={k.label} className="admin-kpi">
            <div className="k-label">{k.label}</div>
            <div className="k-value">{k.value}</div>
            <div className={`k-delta ${k.up ? 'up' : 'down'}`}>{k.up ? '↑ ' : '⚠ '}{k.delta}</div>
          </div>
        ))}
      </div>
      <div className="admin-grid2">
        <div className="admin-card">
          <div className="ac-title">📈 近 7 日新增用户</div>
          <LineChart series={s.userTrend} labels={['一', '二', '三', '四', '五', '六', '日']} width={420} height={180} />
        </div>
        <div className="admin-card">
          <div className="ac-title">📈 近 7 日新增岗位</div>
          <LineChart series={s.jobTrend} labels={['一', '二', '三', '四', '五', '六', '日']} width={420} height={180} color="#10AEFF" />
        </div>
      </div>
      <div className="admin-card">
        <div className="ac-title">⚠️ 风险告警</div>
        <table className="admin-table">
          <thead><tr><th>类型</th><th>对象</th><th>说明</th><th>操作</th></tr></thead>
          <tbody>
            <tr><td><span className="a-tag block">高风险</span></td><td>深圳XX金融集团</td><td>AI 初筛命中假冒企业风险</td><td><span className="a-btn sm danger">去处理</span></td></tr>
            <tr><td><span className="a-tag warn">合规</span></td><td>广州云创数据</td><td>岗位含歧视性用语</td><td><span className="a-btn sm">去处理</span></td></tr>
          </tbody>
        </table>
      </div>
    </>
  )
}

function Review() {
  const navigate = useNavigate()
  const toast = useToast()
  const [queue, setQueue] = useState(adminReviewQueue)
  const [certQueue, setCertQueue] = useState([])
  const [certLoading, setCertLoading] = useState(false)
  const [certError, setCertError] = useState('')
  const [certStatusFilter, setCertStatusFilter] = useState('pending')
  const [certTotal, setCertTotal] = useState(0)
  const tagCls = { pass: 'pass', warning: 'warn', block: 'block' }
  const tagText = { pass: 'AI通过', warning: 'AI警告', block: 'AI拦截' }
  const act = (id, ok) => { setQueue(q => q.filter(x => x.id !== id)); toast(ok ? '已通过' : '已驳回') }

  useEffect(() => {
    loadCertQueue(certStatusFilter)
  }, [certStatusFilter])

  const loadCertQueue = async (statusFilter = certStatusFilter) => {
    try {
      setCertLoading(true)
      const params = { skip: 0, limit: 50 }
      if (statusFilter !== 'all') {
        params.status = statusFilter
      }
      const data = await listCompanyCertifications(params)
      const items = data.items || []
      setCertQueue(items)
      setCertTotal(data.total ?? items.length)
      setCertError('')
    } catch (error) {
      setCertError(error.message || '企业认证审核列表加载失败')
    } finally {
      setCertLoading(false)
    }
  }

  const reviewCert = async (id, action) => {
    try {
      const payload = action === 'approve'
        ? { action: 'approve' }
        : { action: 'reject', reject_reason: '营业执照或企业信息需补充核对' }
      await reviewCompanyCertification(id, payload)
      await loadCertQueue(certStatusFilter)
      toast(action === 'approve' ? '企业认证已通过' : '企业认证已驳回')
    } catch (error) {
      toast(error.message || '审核失败')
    }
  }

  const activeCertFilter = CERT_STATUS_FILTERS.find(f => f.key === certStatusFilter)
  const getCertStatusMeta = status => CERT_STATUS_META[status] || { label: status || '-', tag: 'gray' }
  const getCertMethodLabel = method => CERT_METHOD_LABELS[method] || '营业执照'
  const emptyCertText = certStatusFilter === 'all'
    ? '暂无企业认证记录'
    : `暂无${activeCertFilter?.label || ''}企业认证`

  return (
    <>
      <div className="admin-card">
        <div className="ac-title admin-section-head">
          <span>企业认证审核</span>
          <span className="tiny muted">{certLoading ? '加载中...' : `当前 ${certQueue.length} / ${certTotal} 条`}</span>
        </div>
        <div className="admin-segment" aria-label="企业认证状态筛选">
          {CERT_STATUS_FILTERS.map(filter => (
            <button
              key={filter.key}
              type="button"
              className={certStatusFilter === filter.key ? 'active' : ''}
              onClick={() => setCertStatusFilter(filter.key)}
            >
              {filter.label}
            </button>
          ))}
        </div>
        {certError && <div style={{ color: '#E54545', fontSize: 13, marginBottom: 12 }}>{certError}</div>}
        {certLoading ? (
          <div style={{ color: 'var(--a-text-2)', padding: 20 }}>加载企业认证申请中...</div>
        ) : (
          <table className="admin-table">
            <thead><tr><th>企业名称</th><th>认证方式</th><th>提交人</th><th>信用代码</th><th>法人</th><th>提交时间</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              {certQueue.map(c => (
                <tr key={c.id}>
                  <td>{c.company_name}<div style={{ color: 'var(--a-text-2)', fontSize: 12 }}>{c.registered_address}</div></td>
                  <td><span className="a-tag blue">{getCertMethodLabel(c.verification_method)}</span></td>
                  <td>{c.recruiter_display_name || '-'}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{c.unified_social_credit_code || '-'}</td>
                  <td>{c.legal_representative || '-'}</td>
                  <td style={{ color: 'var(--a-text-2)' }}>{c.created_at ? new Date(c.created_at).toLocaleString() : '-'}</td>
                  <td><span className={`a-tag ${getCertStatusMeta(c.status).tag}`}>{getCertStatusMeta(c.status).label}</span></td>
                  <td>
                    <span className="a-btn sm" onClick={() => navigate(`/admin/company-certification/${c.id}`)}>查看详情</span>
                    {c.status === 'pending' && (
                      <>
                        <span className="a-btn sm primary" style={{ marginLeft: 6 }} onClick={() => reviewCert(c.id, 'approve')}>通过</span>
                        <span className="a-btn sm danger" style={{ marginLeft: 6 }} onClick={() => reviewCert(c.id, 'reject')}>驳回</span>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {certQueue.length === 0 && <tr><td colSpan="8" style={{ textAlign: 'center', color: 'var(--a-text-2)', padding: 24 }}>{emptyCertText}</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      <div className="admin-card" style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', gap: 16 }}>
        <span className="a-tag pass">AI 自动通过率 62%</span>
        <span className="a-tag gray">待人工复核 {queue.length}</span>
        <span style={{ marginLeft: 'auto', color: 'var(--a-text-2)', fontSize: 13 }}>⚡ AI 多模态预审已对全部内容初筛，仅低置信/有风险项进入人工队列</span>
      </div>
      <div className="admin-card">
        <div className="ac-title">审核队列</div>
        <table className="admin-table">
          <thead><tr><th>类型</th><th>对象</th><th>提交人</th><th>AI 预审</th><th>AI 说明</th><th>时间</th><th>操作</th></tr></thead>
          <tbody>
            {queue.map(r => (
              <tr key={r.id}>
                <td><span className={`a-risk-dot ${r.risk}`} />{r.type}</td>
                <td>{r.company}{r.job && <div style={{ color: 'var(--a-text-2)', fontSize: 12 }}>{r.job}</div>}</td>
                <td>{r.submitter}</td>
                <td><span className={`a-tag ${tagCls[r.aiResult]}`}>{tagText[r.aiResult]}</span></td>
                <td style={{ maxWidth: 240, color: 'var(--a-text-2)' }}>{r.aiNote}</td>
                <td style={{ color: 'var(--a-text-2)' }}>{r.time}</td>
                <td>
                  <span className="a-btn sm primary" onClick={() => navigate(`/admin/review/${r.id}`)}>查看详情</span>
                </td>
              </tr>
            ))}
            {queue.length === 0 && <tr><td colSpan="7" style={{ textAlign: 'center', color: 'var(--a-text-2)', padding: 30 }}>队列已清空 🎉</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  )
}

function Users() {
  return (
    <div className="admin-card">
      <div className="ac-title">用户管理</div>
      <table className="admin-table">
        <thead><tr><th>名称</th><th>角色</th><th>认证</th><th>状态</th><th>发布岗位</th><th>注册时间</th><th>操作</th></tr></thead>
        <tbody>
          {adminUsers.map(u => (
            <tr key={u.id}>
              <td>{u.name}</td>
              <td><span className="a-tag blue">{u.role}</span></td>
              <td>{u.verified ? <span className="a-tag pass">已认证</span> : <span className="a-tag gray">未认证</span>}</td>
              <td>{u.status === '风险' ? <span className="a-tag block">风险</span> : <span className="a-tag pass">正常</span>}</td>
              <td>{u.jobs}</td>
              <td style={{ color: 'var(--a-text-2)' }}>{u.date}</td>
              <td><span className="a-btn sm">详情</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function AIMonitor() {
  const toast = useToast()
  const [prompt, setPrompt] = useState(null)
  const [versions, setVersions] = useState([])
  const [loadingPrompt, setLoadingPrompt] = useState(false)
  const [savingPrompt, setSavingPrompt] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [sampleJob, setSampleJob] = useState({
    title: '后端开发工程师',
    city: '杭州',
    salary_min: 20,
    salary_max: 35,
    experience: '3-5年',
    education: '本科',
    description: '负责招聘平台后端核心接口开发、数据建模、审核流状态流转和服务稳定性优化。',
    requirement: '熟悉 Python 和 FastAPI，理解数据库设计、接口鉴权、权限控制和线上问题定位。',
    benefits: '五险一金、双休、带薪年假',
    tags: ['后端开发', 'Python', 'FastAPI'],
  })

  useEffect(() => {
    loadPrompt()
  }, [])

  const loadPrompt = async () => {
    try {
      setLoadingPrompt(true)
      const active = await getActivePromptConfig()
      const list = await listPromptConfigs()
      setPrompt(active)
      setVersions(list.items || [])
    } catch (error) {
      toast(error.message || '提示词配置加载失败')
    } finally {
      setLoadingPrompt(false)
    }
  }

  const updatePrompt = (field, value) => setPrompt(p => ({ ...p, [field]: value }))
  const updateSampleJob = (field, value) => setSampleJob(j => ({ ...j, [field]: value }))

  const testCurrentPrompt = async () => {
    if (!prompt) return
    try {
      const result = await testPromptConfig({
        system_prompt: prompt.system_prompt,
        user_prompt_template: prompt.user_prompt_template,
        output_schema: prompt.output_schema,
        job: sampleJob,
      })
      setTestResult(result)
      toast('测试完成', '✓')
    } catch (error) {
      toast(error.message || '提示词测试失败')
    }
  }

  const saveAndPublishPrompt = async () => {
    if (!prompt) return
    try {
      setSavingPrompt(true)
      const created = await createPromptConfig({
        scenario_key: 'job_content_review',
        name: prompt.name || '岗位内容预审',
        system_prompt: prompt.system_prompt,
        user_prompt_template: prompt.user_prompt_template,
        output_schema: prompt.output_schema,
      })
      await publishPromptConfig(created.id)
      await loadPrompt()
      toast('提示词已发布启用', '✓')
    } catch (error) {
      toast(error.message || '提示词发布失败')
    } finally {
      setSavingPrompt(false)
    }
  }

  return (
    <>
      <div className="admin-kpis">
        <div className="admin-kpi"><div className="k-label">今日 AI 调用</div><div className="k-value">24,724</div><div className="k-delta up">↑ 8.2%</div></div>
        <div className="admin-kpi"><div className="k-label">平均响应</div><div className="k-value">1.9s</div><div className="k-delta up">P95 ＜ 3s</div></div>
        <div className="admin-kpi"><div className="k-label">降级触发</div><div className="k-value">12</div><div className="k-delta up">占比 0.05%</div></div>
        <div className="admin-kpi"><div className="k-label">今日成本</div><div className="k-value">¥186</div><div className="k-delta up">预算内</div></div>
      </div>
      <div className="admin-card">
        <div className="ac-title">⚡ 各 AI 能力运行状态</div>
        <table className="admin-table">
          <thead><tr><th>能力</th><th>调用量</th><th>质量指标</th><th>平均耗时</th><th>状态</th></tr></thead>
          <tbody>
            {adminAIMetrics.map(m => (
              <tr key={m.name}>
                <td>{m.name}</td><td>{m.calls}</td><td>{m.accuracy}</td><td>{m.avgTime}</td>
                <td>{m.status === 'good' ? <span className="a-tag pass">正常</span> : <span className="a-tag warn">关注</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="admin-card">
        <div className="ac-title admin-section-head">
          <span>提示词管理 · 岗位内容预审</span>
          <span className="tiny muted">{loadingPrompt ? '加载中...' : `当前版本 v${prompt?.version || '-'}`}</span>
        </div>
        {prompt && (
          <div className="prompt-grid">
            <div className="prompt-editor">
              <label>名称</label>
              <input value={prompt.name || ''} onChange={e => updatePrompt('name', e.target.value)} />
              <label>System Prompt</label>
              <textarea value={prompt.system_prompt || ''} onChange={e => updatePrompt('system_prompt', e.target.value)} />
              <label>User Prompt 模板</label>
              <textarea value={prompt.user_prompt_template || ''} onChange={e => updatePrompt('user_prompt_template', e.target.value)} />
              <label>输出 JSON Schema 说明</label>
              <textarea value={prompt.output_schema || ''} onChange={e => updatePrompt('output_schema', e.target.value)} />
              <div className="row" style={{ gap: 8, marginTop: 12 }}>
                <button className="a-btn" onClick={testCurrentPrompt}>测试提示词</button>
                <button className={`a-btn primary ${savingPrompt ? 'disabled' : ''}`} onClick={saveAndPublishPrompt} disabled={savingPrompt}>
                  {savingPrompt ? '发布中...' : '保存为新版本并启用'}
                </button>
              </div>
            </div>
            <div className="prompt-test">
              <div className="tiny muted" style={{ marginBottom: 8 }}>测试岗位样例</div>
              <input value={sampleJob.title} onChange={e => updateSampleJob('title', e.target.value)} />
              <div className="row" style={{ gap: 8 }}>
                <input value={sampleJob.city} onChange={e => updateSampleJob('city', e.target.value)} />
                <input value={sampleJob.experience} onChange={e => updateSampleJob('experience', e.target.value)} />
              </div>
              <textarea value={sampleJob.description} onChange={e => updateSampleJob('description', e.target.value)} />
              <textarea value={sampleJob.requirement} onChange={e => updateSampleJob('requirement', e.target.value)} />
              {testResult && (
                <div className="prompt-result">
                  <div><span className={`a-tag ${testResult.level === 'pass' ? 'pass' : testResult.level === 'warning' ? 'warn' : 'block'}`}>{testResult.level}</span></div>
                  <div style={{ marginTop: 8 }}>{testResult.summary}</div>
                  {(testResult.findings || []).map((f, idx) => (
                    <div key={idx} className="tiny muted" style={{ marginTop: 6 }}>
                      {f.category}：{f.evidence || '-'}；{f.suggestion}
                    </div>
                  ))}
                </div>
              )}
              <div className="tiny muted" style={{ marginTop: 14 }}>历史版本</div>
              <table className="admin-table">
                <tbody>
                  {versions.map(v => (
                    <tr key={v.id || `default-${v.version}`}>
                      <td>v{v.version}</td>
                      <td>{v.name}</td>
                      <td>{v.is_active ? <span className="a-tag pass">启用</span> : <span className="a-tag gray">历史</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

function BaseData() {
  return (
    <div className="admin-card">
      <div className="ac-title row" style={{ justifyContent: 'space-between' }}><span>🗂 标准职位库</span><span className="a-btn sm primary" style={{ marginLeft: 'auto' }}>＋ 新增职位</span></div>
      <table className="admin-table">
        <thead><tr><th>标准名称</th><th>分类</th><th>别名（AI 标准化映射）</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          {adminJobLib.map(j => (
            <tr key={j.id}>
              <td>{j.name}</td><td>{j.category}</td>
              <td style={{ color: 'var(--a-text-2)' }}>{j.alias}</td>
              <td><span className="a-tag pass">{j.status}</span></td>
              <td><span className="a-btn sm">编辑</span> <span className="a-btn sm">停用</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
