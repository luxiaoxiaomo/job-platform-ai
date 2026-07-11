import React, { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useToast } from '../components/ui.jsx'
import { LineChart, ScoreBar } from '../components/charts.jsx'
import { adminStats, adminAIMetrics, reviewQueue as adminReviewQueue } from '../mock/data.js'
import {
  createPromptConfig,
  getActivePromptConfig,
  listJobsForAdmin,
  listCompanyCertifications,
  listPromptConfigs,
  preReviewJobContent,
  publishPromptConfig,
  reviewJob,
  reviewCompanyCertification,
  testPromptConfig,
  getDefaultMatchRuleConfig,
  getAdminApplicationStats,
  getAdminBusinessLoopStats,
  getAdminOperationsStats,
  getContactExchangeStats,
  getCurrentUser,
  listAdminNotificationPushTasks,
  listUsersForAdmin,
  logout,
  runAdminNotificationPushWorker,
  updateAdminNotificationPushTaskStatus,
  createTagLibraryItem,
  createStandardPosition,
  listTagLibraryItems,
  listBaseDataOperationLogs,
  listStandardPositions,
  updateTagLibraryItem,
  updateStandardPosition,
} from '../services/index.js'
import '../styles/admin.css'

const NAV = [
  { key: 'dash', icon: '📊', label: '数据概览' },
  { key: 'review', icon: '✅', label: '审核管理' },
  { key: 'users', icon: '👥', label: '用户管理' },
  { key: 'ai', icon: '⚡', label: 'AI 监控' },
  { key: 'data-overview', icon: '🗂', label: '基础数据概览' },
  { key: 'data-positions', icon: '💼', label: '标准职位库' },
  { key: 'data-tags', icon: '🏷', label: '标签库', path: '/admin/tags' },
  { key: 'data-rules', icon: '🎯', label: '匹配规则' },
  { key: 'data-logs', icon: '🧾', label: '操作日志' },
  { key: 'data-push', icon: '🔔', label: '推送队列' },
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
  const navigate = useNavigate()
  const location = useLocation()
  const [page, setPage] = useState(location.state?.page || 'dash')
  const currentUser = getCurrentUser()
  const adminName = currentUser?.display_name || currentUser?.phone || 'admin'
  const title = NAV.find(n => n.key === page)?.label || '运营后台'

  const openNavItem = (item) => {
    if (item.path) {
      navigate(item.path)
      return
    }
    setPage(item.key)
  }

  useEffect(() => {
    if (location.state?.page) {
      setPage(location.state.page)
    }
  }, [location.state])

  return (
    <div className="admin">
      <aside className="admin-side">
        <div className="admin-brand"><span className="dot" />空岗平台 · 运营后台</div>
        <nav className="admin-nav">
          {NAV.map(n => (
            <div key={n.key} className={`nav-item ${page === n.key ? 'active' : ''}`} onClick={() => openNavItem(n)}>
              <span className="ico">{n.icon}</span>{n.label}
            </div>
          ))}
        </nav>
        <div className="admin-side-foot" onClick={() => navigate('/')}>← 返回原型首页</div>
      </aside>
      <main className="admin-main">
        <header className="admin-topbar">
          <span className="at-title">{title}</span>
          <div className="at-right">
            <span>🔔</span>
            <span>管理员 · {adminName}</span>
            <button type="button" className="a-btn sm" onClick={logout}>退出登录</button>
          </div>
        </header>
        <div className="admin-content">
          {page === 'dash' && <Dash />}
          {page === 'review' && <ReviewRealV2 />}
          {page === 'users' && <Users />}
          {page === 'ai' && <AIMonitor />}
          {page === 'data-overview' && <BaseData section="overview" setPage={setPage} />}
          {page === 'data-positions' && <BaseData section="positions" setPage={setPage} />}
          {page === 'data-tags' && <BaseData section="tags" setPage={setPage} />}
          {page === 'data-rules' && <BaseData section="rules" setPage={setPage} />}
          {page === 'data-logs' && <BaseDataOperationLogs />}
          {page === 'data-push' && <PushQueueCard />}
        </div>
      </main>
    </div>
  )
}


function Dash() {
  const s = adminStats
  const [operationsStats, setOperationsStats] = useState(null)
  const [operationsLoading, setOperationsLoading] = useState(true)
  const [operationsError, setOperationsError] = useState('')
  const [exchangeStats, setExchangeStats] = useState(null)
  const [applicationStats, setApplicationStats] = useState(null)
  const [applicationStatsLoading, setApplicationStatsLoading] = useState(true)
  const [applicationStatsError, setApplicationStatsError] = useState('')
  const [businessStats, setBusinessStats] = useState(null)
  const [businessStatsLoading, setBusinessStatsLoading] = useState(true)
  const [businessStatsError, setBusinessStatsError] = useState('')

  useEffect(() => {
    let alive = true
    setOperationsLoading(true)
    getAdminOperationsStats()
      .then(data => {
        if (!alive) return
        setOperationsStats(data)
        setOperationsError('')
      })
      .catch(err => {
        if (!alive) return
        setOperationsStats(null)
        setOperationsError(err.message || '运营统计加载失败')
      })
      .finally(() => {
        if (alive) setOperationsLoading(false)
      })
    getContactExchangeStats()
      .then(data => {
        if (alive) setExchangeStats(data)
      })
      .catch(() => {
        if (alive) setExchangeStats(null)
      })
    setApplicationStatsLoading(true)
    getAdminApplicationStats()
      .then(data => {
        if (!alive) return
        setApplicationStats(data)
        setApplicationStatsError('')
      })
      .catch(err => {
        if (!alive) return
        setApplicationStats(null)
        setApplicationStatsError(err.message || '平台投递统计加载失败')
      })
      .finally(() => {
        if (alive) setApplicationStatsLoading(false)
      })
    setBusinessStatsLoading(true)
    getAdminBusinessLoopStats()
      .then(data => {
        if (!alive) return
        setBusinessStats(data)
        setBusinessStatsError('')
      })
      .catch(err => {
        if (!alive) return
        setBusinessStats(null)
        setBusinessStatsError(err.message || '平台业务闭环统计加载失败')
      })
      .finally(() => {
        if (alive) setBusinessStatsLoading(false)
      })
    return () => { alive = false }
  }, [])

  return (
    <>
      <div className="admin-card">
        <div className="ac-title">平台运营总览</div>
        {operationsError ? (
          <div style={{ color: '#E54545', fontSize: 13 }}>{operationsError}</div>
        ) : (
          <div className="admin-kpis" style={{ marginBottom: 0 }}>
            {[
              ['今日新增用户', operationsStats?.today_new_user_count ?? 0],
              ['今日新增岗位', operationsStats?.today_new_job_count ?? 0],
              ['今日新增投递', operationsStats?.today_new_application_count ?? 0],
              ['活跃岗位', operationsStats?.active_job_count ?? 0],
              ['待审核岗位', operationsStats?.pending_job_review_count ?? 0],
              ['有效对接', exchangeStats?.accepted_count ?? 0],
            ].map(([label, value]) => (
              <div key={label} className="admin-kpi">
                <div className="k-label">{label}</div>
                <div className="k-value">{operationsLoading ? '...' : value}</div>
                <div className="k-delta up">real API</div>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="admin-kpis">
        {s.kpis.map(k => (
          <div key={k.label} className="admin-kpi">
            <div className="k-label">{k.label}</div>
            <div className="k-value">{k.value}</div>
            <div className={`k-delta ${k.up ? 'up' : 'down'}`}>{k.up ? '↑ ' : '⚠ '}{k.delta}</div>
          </div>
        ))}
      </div>
      <div className="admin-card">
        <div className="ac-title">真实业务闭环 · 有效对接</div>
        {businessStatsError ? (
          <div style={{ color: '#E54545', fontSize: 13 }}>{businessStatsError}</div>
        ) : (
          <div className="admin-kpis" style={{ gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', marginBottom: 0 }}>
            {[
              ['成功对接', businessStats?.successful_connection_count ?? exchangeStats?.accepted_count ?? 0],
              ['待确认交换', businessStats?.pending_exchange_count ?? exchangeStats?.pending_count ?? 0],
              ['已拒绝交换', businessStats?.declined_exchange_count ?? exchangeStats?.declined_count ?? 0],
              ['交换请求总数', businessStats?.contact_exchange_count ?? exchangeStats?.total_count ?? 0],
            ].map(([label, value]) => (
              <div key={label} className="admin-kpi">
                <div className="k-label">{label}</div>
                <div className="k-value">{businessStatsLoading ? '...' : value}</div>
                <div className="k-delta up">real API</div>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="admin-card">
        <div className="ac-title">真实业务闭环 · 平台投递处理</div>
        {applicationStatsError ? (
          <div style={{ color: '#E54545', fontSize: 13 }}>{applicationStatsError}</div>
        ) : (
          <div className="admin-kpis" style={{ gridTemplateColumns: 'repeat(6, minmax(0, 1fr))', marginBottom: 0 }}>
            {[
              ['投递总数', businessStats?.application_count ?? applicationStats?.total_count ?? 0],
              ['新投递', businessStats?.submitted_count ?? applicationStats?.submitted_count ?? 0],
              ['已查看', businessStats?.viewed_count ?? applicationStats?.viewed_count ?? 0],
              ['已邀面', businessStats?.interview_invited_count ?? applicationStats?.interview_invited_count ?? 0],
              ['已录用', businessStats?.hired_count ?? applicationStats?.hired_count ?? 0],
              ['已拒绝', businessStats?.rejected_count ?? applicationStats?.rejected_count ?? 0],
            ].map(([label, value]) => (
              <div key={label} className="admin-kpi">
                <div className="k-label">{label}</div>
                <div className="k-value">{applicationStatsLoading && businessStatsLoading ? '...' : value}</div>
                <div className="k-delta up">real API</div>
              </div>
            ))}
          </div>
        )}
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
  const [users, setUsers] = useState([])
  const [role, setRole] = useState('')
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadUsers = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await listUsersForAdmin({ limit: 50, ...(role ? { role } : {}) })
      setUsers(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      setUsers([])
      setTotal(0)
      setError(err.message || '用户列表加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [role])

  const roleLabel = {
    seeker: '求职者',
    recruiter: '招聘者',
    admin: '管理员',
  }

  return (
    <div className="admin-card">
      <div className="ac-title row" style={{ justifyContent: 'space-between' }}>
        <span>用户管理</span>
        <div className="row" style={{ gap: 8, marginLeft: 'auto' }}>
          {[
            ['', '全部'],
            ['seeker', '求职者'],
            ['recruiter', '招聘者'],
            ['admin', '管理员'],
          ].map(([value, label]) => (
            <button key={value || 'all'} type="button" className={`a-btn sm ${role === value ? 'primary' : ''}`} onClick={() => setRole(value)}>
              {label}
            </button>
          ))}
          <button type="button" className="a-btn sm" onClick={loadUsers}>刷新</button>
        </div>
      </div>
      <div className="tiny muted" style={{ marginBottom: 10 }}>真实用户资源，共 {total} 条</div>
      {error && <div style={{ color: '#E54545', fontSize: 13, marginBottom: 12 }}>{error}</div>}
      <table className="admin-table">
        <thead><tr><th>ID</th><th>名称</th><th>手机号</th><th>角色</th><th>状态</th><th>注册时间</th><th>操作</th></tr></thead>
        <tbody>
          {loading ? (
            <tr><td colSpan="7" style={{ color: 'var(--a-text-2)', padding: 24 }}>加载用户中...</td></tr>
          ) : users.length > 0 ? users.map(u => (
            <tr key={u.id}>
              <td>{u.id}</td>
              <td>{u.display_name || '-'}</td>
              <td>{u.phone}</td>
              <td><span className="a-tag blue">{roleLabel[u.role] || u.role}</span></td>
              <td><span className={`a-tag ${u.status === 'active' ? 'pass' : 'gray'}`}>{u.status === 'active' ? '正常' : u.status}</span></td>
              <td style={{ color: 'var(--a-text-2)' }}>{u.created_at ? new Date(u.created_at).toLocaleString('zh-CN') : '-'}</td>
              <td><span className="a-btn sm">详情</span></td>
            </tr>
          )) : (
            <tr><td colSpan="7" style={{ color: 'var(--a-text-2)', padding: 24 }}>暂无用户</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

function ReviewReal() {
  const navigate = useNavigate()
  const toast = useToast()
  const [jobs, setJobs] = useState([])
  const [jobsLoading, setJobsLoading] = useState(false)
  const [jobsError, setJobsError] = useState('')
  const [expandedJobId, setExpandedJobId] = useState(null)
  const [certQueue, setCertQueue] = useState([])
  const [certLoading, setCertLoading] = useState(false)
  const [certError, setCertError] = useState('')
  const [certStatusFilter, setCertStatusFilter] = useState('pending')

  useEffect(() => {
    loadJobs()
  }, [])

  useEffect(() => {
    loadCerts(certStatusFilter)
  }, [certStatusFilter])

  const loadJobs = async () => {
    try {
      setJobsLoading(true)
      const data = await listJobsForAdmin({ status: 'pending', skip: 0, limit: 50 })
      const items = data.items || []
      const jobsWithReview = await Promise.all(items.map(async job => {
        try {
          const aiReview = await preReviewJobContent(job)
          return { ...job, aiReview }
        } catch (error) {
          return {
            ...job,
            aiReviewError: error.message || 'AI pre-review failed',
            aiReview: {
              level: 'warning',
              summary: 'AI 预审暂不可用，请人工复核岗位内容。',
              findings: [],
            },
          }
        }
      }))
      setJobs(jobsWithReview)
      setJobsError('')
    } catch (error) {
      setJobsError(error.message || '岗位列表加载失败')
    } finally {
      setJobsLoading(false)
    }
  }

  const loadCerts = async (statusFilter = certStatusFilter) => {
    try {
      setCertLoading(true)
      const params = { skip: 0, limit: 50 }
      if (statusFilter !== 'all') params.status = statusFilter
      const data = await listCompanyCertifications(params)
      setCertQueue(data.items || [])
      setCertError('')
    } catch (error) {
      setCertError(error.message || '企业认证列表加载失败')
    } finally {
      setCertLoading(false)
    }
  }

  const reviewPendingJob = async (jobId, action) => {
    try {
      await reviewJob(jobId, action === 'approve'
        ? { action: 'approve' }
        : { action: 'reject', reject_reason: '岗位内容需要补充或调整后重新提交' })
      await loadJobs()
      toast(action === 'approve' ? '岗位已通过' : '岗位已驳回')
    } catch (error) {
      toast(error.message || '岗位审核失败')
    }
  }

  const reviewCert = async (id, action) => {
    try {
      await reviewCompanyCertification(id, action === 'approve'
        ? { action: 'approve' }
        : { action: 'reject', reject_reason: '企业认证材料需要补充' })
      await loadCerts(certStatusFilter)
      toast(action === 'approve' ? '企业认证已通过' : '企业认证已驳回')
    } catch (error) {
      toast(error.message || '企业认证审核失败')
    }
  }

  return (
    <>
      <div className="admin-card">
        <div className="ac-title admin-section-head">
          <span>岗位发布审核</span>
          <span className="tiny muted">{jobsLoading ? '加载中...' : `待审 ${jobs.length} 条`}</span>
        </div>
        {jobsError && <div style={{ color: '#E54545', fontSize: 13, marginBottom: 12 }}>{jobsError}</div>}
        {jobsLoading ? (
          <div style={{ color: 'var(--a-text-2)', padding: 20 }}>加载岗位列表中...</div>
        ) : (
          <table className="admin-table">
            <thead><tr><th>岗位</th><th>企业</th><th>城市</th><th>薪资</th><th>经验/学历</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              {jobs.map(job => (
                <tr key={job.id}>
                  <td>{job.title}<div style={{ color: 'var(--a-text-2)', fontSize: 12, maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{job.description}</div></td>
                  <td>{job.recruiter_display_name || '-'}</td>
                  <td>{job.city}</td>
                  <td>{job.salary_min}-{job.salary_max}K</td>
                  <td>{job.experience} / {job.education}</td>
                  <td><span className="a-tag warn">{job.status}</span></td>
                  <td>
                    <span className="a-btn sm primary" onClick={() => reviewPendingJob(job.id, 'approve')}>通过</span>
                    <span className="a-btn sm danger" style={{ marginLeft: 6 }} onClick={() => reviewPendingJob(job.id, 'reject')}>驳回</span>
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && <tr><td colSpan="7" style={{ textAlign: 'center', color: 'var(--a-text-2)', padding: 30 }}>暂无待审核岗位</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      <div className="admin-card">
        <div className="ac-title admin-section-head">
          <span>企业认证审核</span>
          <span className="tiny muted">{certLoading ? '加载中...' : `当前 ${certQueue.length} 条`}</span>
        </div>
        <div className="admin-segment">
          {['pending', 'approved', 'rejected'].map(s => (
            <button key={s} type="button" className={certStatusFilter === s ? 'active' : ''} onClick={() => setCertStatusFilter(s)}>{s}</button>
          ))}
        </div>
        {certError && <div style={{ color: '#E54545', fontSize: 13, marginBottom: 12 }}>{certError}</div>}
        {certLoading ? (
          <div style={{ color: 'var(--a-text-2)', padding: 20 }}>加载企业认证中...</div>
        ) : (
          <table className="admin-table">
            <thead><tr><th>企业</th><th>提交人</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              {certQueue.map(c => (
                <tr key={c.id}>
                  <td>{c.company_name}</td>
                  <td>{c.recruiter_display_name || '-'}</td>
                  <td><span className="a-tag blue">{c.status}</span></td>
                  <td>
                    <span className="a-btn sm" onClick={() => navigate(`/admin/company-certification/${c.id}`)}>详情</span>
                    {c.status === 'pending' && (
                      <>
                        <span className="a-btn sm primary" style={{ marginLeft: 6 }} onClick={() => reviewCert(c.id, 'approve')}>通过</span>
                        <span className="a-btn sm danger" style={{ marginLeft: 6 }} onClick={() => reviewCert(c.id, 'reject')}>驳回</span>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {certQueue.length === 0 && <tr><td colSpan="4" style={{ textAlign: 'center', color: 'var(--a-text-2)', padding: 30 }}>暂无企业认证</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}

function ReviewRealV2() {
  const navigate = useNavigate()
  const toast = useToast()
  const [jobs, setJobs] = useState([])
  const [jobsLoading, setJobsLoading] = useState(false)
  const [jobsError, setJobsError] = useState('')
  const [expandedJobId, setExpandedJobId] = useState(null)
  const [certs, setCerts] = useState([])
  const [certLoading, setCertLoading] = useState(false)
  const [certError, setCertError] = useState('')
  const [certStatus, setCertStatus] = useState('pending')

  useEffect(() => {
    loadJobs()
  }, [])

  useEffect(() => {
    loadCerts(certStatus)
  }, [certStatus])

  const loadJobs = async () => {
    try {
      setJobsLoading(true)
      const data = await listJobsForAdmin({ status: 'pending', skip: 0, limit: 50 })
      const items = data.items || []
      const reviewed = await Promise.all(items.map(async job => {
        try {
          const aiReview = await preReviewJobContent(job)
          return { ...job, aiReview }
        } catch (error) {
          return {
            ...job,
            aiReviewError: error.message || 'AI 预审失败',
            aiReview: {
              level: 'warning',
              summary: 'AI 预审暂不可用，请人工复核岗位内容。',
              findings: [],
              prompt_version: null,
              prompt_source: 'fallback',
            },
          }
        }
      }))
      setJobs(reviewed)
      setJobsError('')
    } catch (error) {
      setJobsError(error.message || '岗位列表加载失败')
    } finally {
      setJobsLoading(false)
    }
  }

  const loadCerts = async (status = certStatus) => {
    try {
      setCertLoading(true)
      const params = { skip: 0, limit: 50 }
      if (status !== 'all') params.status = status
      const data = await listCompanyCertifications(params)
      setCerts(data.items || [])
      setCertError('')
    } catch (error) {
      setCertError(error.message || '企业认证列表加载失败')
    } finally {
      setCertLoading(false)
    }
  }

  const reviewPendingJob = async (jobId, action) => {
    try {
      await reviewJob(jobId, action === 'approve'
        ? { action: 'approve' }
        : { action: 'reject', reject_reason: '岗位内容需要补充或调整后重新提交' })
      await loadJobs()
      toast(action === 'approve' ? '岗位已通过' : '岗位已驳回')
    } catch (error) {
      toast(error.message || '岗位审核失败')
    }
  }

  const reviewCert = async (id, action) => {
    try {
      await reviewCompanyCertification(id, action === 'approve'
        ? { action: 'approve' }
        : { action: 'reject', reject_reason: '企业认证材料需要补充' })
      await loadCerts(certStatus)
      toast(action === 'approve' ? '企业认证已通过' : '企业认证已驳回')
    } catch (error) {
      toast(error.message || '企业认证审核失败')
    }
  }

  const aiTag = review => {
    if (review?.level === 'pass') return { cls: 'pass', text: '建议通过' }
    if (review?.level === 'block') return { cls: 'block', text: '建议拦截' }
    return { cls: 'warn', text: '人工复核' }
  }

  return (
    <>
      <div className="admin-card">
        <div className="ac-title admin-section-head">
          <span>岗位发布审核</span>
          <span className="tiny muted">{jobsLoading ? '加载中...' : `待审 ${jobs.length} 条`}</span>
        </div>
        {jobsError && <div style={{ color: '#E54545', fontSize: 13, marginBottom: 12 }}>{jobsError}</div>}
        {jobsLoading ? (
          <div style={{ color: 'var(--a-text-2)', padding: 20 }}>加载岗位列表和 AI 预审结果中...</div>
        ) : (
          <table className="admin-table">
            <thead><tr><th>岗位</th><th>企业</th><th>城市</th><th>薪资</th><th>AI 预审</th><th>风险说明</th><th>操作</th></tr></thead>
            <tbody>
              {jobs.map(job => {
                const review = job.aiReview || {}
                const tag = aiTag(review)
                const expanded = expandedJobId === job.id
                return (
                  <React.Fragment key={job.id}>
                    <tr>
                      <td>
                        <strong>{job.title}</strong>
                        <div style={{ color: 'var(--a-text-2)', fontSize: 12 }}>{job.experience} / {job.education}</div>
                      </td>
                      <td>{job.recruiter_display_name || '-'}</td>
                      <td>{job.city}</td>
                      <td>{job.salary_min}-{job.salary_max}K</td>
                      <td>
                        <span className={`a-tag ${tag.cls}`}>{tag.text}</span>
                        <div className="tiny muted" style={{ marginTop: 4 }}>v{review.prompt_version || '-'} · {review.prompt_source || 'rules'}</div>
                      </td>
                      <td style={{ maxWidth: 280 }}>
                        <div style={{ color: 'var(--a-text-2)' }}>{review.summary || '-'}</div>
                        {job.aiReviewError && <div className="tiny" style={{ color: '#E54545', marginTop: 4 }}>{job.aiReviewError}</div>}
                      </td>
                      <td>
                        <span className="a-btn sm" onClick={() => setExpandedJobId(expanded ? null : job.id)}>{expanded ? '收起' : '详情'}</span>
                        <span className="a-btn sm primary" style={{ marginLeft: 6 }} onClick={() => reviewPendingJob(job.id, 'approve')}>通过</span>
                        <span className="a-btn sm danger" style={{ marginLeft: 6 }} onClick={() => reviewPendingJob(job.id, 'reject')}>驳回</span>
                      </td>
                    </tr>
                    {expanded && (
                      <tr>
                        <td colSpan="7" style={{ background: '#FAFBFC' }}>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                            <div>
                              <div className="tiny muted" style={{ marginBottom: 6 }}>岗位职责</div>
                              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{job.description}</div>
                            </div>
                            <div>
                              <div className="tiny muted" style={{ marginBottom: 6 }}>任职要求</div>
                              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{job.requirement}</div>
                            </div>
                          </div>
                          {(review.findings || []).length > 0 ? (
                            <div style={{ marginTop: 14 }}>
                              <div className="tiny muted" style={{ marginBottom: 6 }}>AI 风险项</div>
                              {(review.findings || []).map((finding, index) => (
                                <div key={index} style={{ marginBottom: 6 }}>
                                  <span className={`a-tag ${finding.severity === 'block' ? 'block' : 'warn'}`}>{finding.category}</span>
                                  <span style={{ marginLeft: 8 }}>{finding.evidence || '-'}</span>
                                  <span style={{ marginLeft: 8, color: 'var(--a-text-2)' }}>{finding.suggestion}</span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="tiny muted" style={{ marginTop: 14 }}>未检测到明显风险项。</div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                )
              })}
              {jobs.length === 0 && <tr><td colSpan="7" style={{ textAlign: 'center', color: 'var(--a-text-2)', padding: 30 }}>暂无待审核岗位</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      <div className="admin-card">
        <div className="ac-title admin-section-head">
          <span>企业认证审核</span>
          <span className="tiny muted">{certLoading ? '加载中...' : `当前 ${certs.length} 条`}</span>
        </div>
        <div className="admin-segment">
          {['pending', 'approved', 'rejected'].map(status => (
            <button key={status} type="button" className={certStatus === status ? 'active' : ''} onClick={() => setCertStatus(status)}>{status}</button>
          ))}
        </div>
        {certError && <div style={{ color: '#E54545', fontSize: 13, marginBottom: 12 }}>{certError}</div>}
        {certLoading ? (
          <div style={{ color: 'var(--a-text-2)', padding: 20 }}>加载企业认证中...</div>
        ) : (
          <table className="admin-table">
            <thead><tr><th>企业</th><th>提交人</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              {certs.map(cert => (
                <tr key={cert.id}>
                  <td>{cert.company_name}</td>
                  <td>{cert.recruiter_display_name || '-'}</td>
                  <td><span className="a-tag blue">{cert.status}</span></td>
                  <td>
                    <span className="a-btn sm" onClick={() => navigate(`/admin/company-certification/${cert.id}`)}>详情</span>
                    {cert.status === 'pending' && (
                      <>
                        <span className="a-btn sm primary" style={{ marginLeft: 6 }} onClick={() => reviewCert(cert.id, 'approve')}>通过</span>
                        <span className="a-btn sm danger" style={{ marginLeft: 6 }} onClick={() => reviewCert(cert.id, 'reject')}>驳回</span>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {certs.length === 0 && <tr><td colSpan="4" style={{ textAlign: 'center', color: 'var(--a-text-2)', padding: 30 }}>暂无企业认证</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </>
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

function PushTaskStatusTag({ status }) {
  const meta = {
    pending: ['warn', '待发送'],
    deferred: ['blue', '延后'],
    digest_placeholder: ['gray', '摘要占位'],
    sent: ['pass', '已发送'],
    failed: ['block', '失败'],
  }[status] || ['gray', status]
  return <span className={`a-tag ${meta[0]}`}>{meta[1]}</span>
}

function PushQueueCard() {
  const toast = useToast()
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await listAdminNotificationPushTasks({ limit: 20, ...(status ? { status } : {}) })
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      setItems([])
      setTotal(0)
      setError(err.message || '推送队列加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [status])

  const mark = async (taskId, nextStatus, errorMessage) => {
    try {
      await updateAdminNotificationPushTaskStatus(taskId, {
        status: nextStatus,
        ...(errorMessage ? { error_message: errorMessage } : {}),
      })
      toast(nextStatus === 'sent' ? '已标记为已发送' : '已标记为失败')
      await load()
    } catch (err) {
      toast(err.message || '更新推送任务失败')
    }
  }

  const runWorker = async () => {
    try {
      setRunning(true)
      const result = await runAdminNotificationPushWorker({ limit: 50 })
      toast(`worker 已处理 ${result.processed_count || 0} 条，摘要 ${result.digest_count || 0} 条`)
      await load()
    } catch (err) {
      toast(err.message || '运行推送 worker 失败')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="admin-card" style={{ marginBottom: 20 }}>
      <div className="ac-title row" style={{ justifyContent: 'space-between' }}>
        <span>推送队列管理</span>
        <div className="row" style={{ gap: 8, marginLeft: 'auto' }}>
          {[
            ['', '全部'],
            ['pending', '待发送'],
            ['deferred', '延后'],
            ['digest_placeholder', '摘要占位'],
            ['sent', '已发送'],
            ['failed', '失败'],
          ].map(([value, label]) => (
            <button key={value || 'all'} type="button" className={`a-btn sm ${status === value ? 'primary' : ''}`} onClick={() => setStatus(value)}>
              {label}
            </button>
          ))}
          <button type="button" className={`a-btn sm primary ${running ? 'disabled' : ''}`} onClick={runWorker} disabled={running}>
            {running ? '运行中...' : '运行 worker'}
          </button>
          <button type="button" className="a-btn sm" onClick={load}>刷新</button>
        </div>
      </div>
      {error ? (
        <div style={{ color: '#E54545', fontSize: 13 }}>{error}</div>
      ) : (
        <>
          <div className="tiny muted" style={{ marginBottom: 10 }}>
            共 {total} 条；当前 worker 会处理到期任务，真实微信发送由后续接入配置启用。
          </div>
          <table className="admin-table">
            <thead><tr><th>ID</th><th>接收人</th><th>状态</th><th>标题</th><th>计划时间</th><th>原因</th><th>操作</th></tr></thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="7" style={{ color: 'var(--a-text-2)' }}>加载中...</td></tr>
              ) : items.length > 0 ? items.map(item => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.recipient_id}</td>
                  <td><PushTaskStatusTag status={item.status} /></td>
                  <td>
                    <div>{item.title}</div>
                    <div className="tiny muted">{item.detail || '-'}</div>
                    {item.error_message && <div className="tiny" style={{ color: '#E54545' }}>{item.error_message}</div>}
                  </td>
                  <td>{item.scheduled_at ? new Date(item.scheduled_at).toLocaleString('zh-CN') : '-'}</td>
                  <td>{item.reason || '-'}</td>
                  <td>
                    {item.status !== 'sent' && <button type="button" className="a-btn sm" onClick={() => mark(item.id, 'sent')}>标记已发送</button>}
                    {item.status !== 'failed' && <button type="button" className="a-btn sm danger" style={{ marginLeft: 6 }} onClick={() => mark(item.id, 'failed', '管理员手动标记失败')}>标记失败</button>}
                  </td>
                </tr>
              )) : (
                <tr><td colSpan="7" style={{ color: 'var(--a-text-2)' }}>暂无推送任务</td></tr>
              )}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}

export function BaseData({ section = 'overview', setPage }) {
  const toast = useToast()
  const navigate = useNavigate()
  const [ruleConfig, setRuleConfig] = useState(null)
  const [ruleLoading, setRuleLoading] = useState(true)
  const [positions, setPositions] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState({
    name: '',
    category: '',
    aliasesText: '',
    description: '',
    status: 'active',
  })
  const [tags, setTags] = useState([])
  const [tagTotal, setTagTotal] = useState(0)
  const [tagLoading, setTagLoading] = useState(true)
  const [tagError, setTagError] = useState('')
  const [editingTagId, setEditingTagId] = useState(null)
  const [tagForm, setTagForm] = useState({
    name: '',
    category: '',
    parentId: '',
    color: '',
    description: '',
    sortOrder: 0,
    status: 'active',
  })

  const loadPositions = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await listStandardPositions({ limit: 100 })
      setPositions(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      setPositions([])
      setTotal(0)
      setError(err.message || '标准职位库加载失败')
    } finally {
      setLoading(false)
    }
  }

  const loadDefaultRule = async () => {
    try {
      setRuleLoading(true)
      const data = await getDefaultMatchRuleConfig()
      setRuleConfig(data)
    } catch (err) {
      console.error('加载默认匹配规则失败:', err)
    } finally {
      setRuleLoading(false)
    }
  }

  const loadTags = async () => {
    try {
      setTagLoading(true)
      setTagError('')
      const data = await listTagLibraryItems({ limit: 100 })
      setTags(data.items || [])
      setTagTotal(data.total || 0)
    } catch (err) {
      setTags([])
      setTagTotal(0)
      setTagError(err.message || '标签库加载失败')
    } finally {
      setTagLoading(false)
    }
  }

  useEffect(() => {
    loadDefaultRule()
    loadPositions()
    loadTags()
  }, [])

  const resetForm = () => {
    setEditingId(null)
    setForm({
      name: '',
      category: '',
      aliasesText: '',
      description: '',
      status: 'active',
    })
  }

  const editPosition = (position) => {
    setEditingId(position.id)
    setForm({
      name: position.name || '',
      category: position.category || '',
      aliasesText: (position.aliases || []).join(', '),
      description: position.description || '',
      status: position.status || 'active',
    })
  }

  const savePosition = async () => {
    const payload = {
      name: form.name.trim(),
      category: form.category.trim(),
      aliases: form.aliasesText.split(',').map(item => item.trim()).filter(Boolean),
      description: form.description.trim() || null,
      status: form.status,
    }
    if (!payload.name || !payload.category) {
      toast('请填写标准名称和分类')
      return
    }

    try {
      if (editingId) {
        await updateStandardPosition(editingId, payload)
        toast('标准职位已更新')
      } else {
        await createStandardPosition(payload)
        toast('标准职位已新增')
      }
      resetForm()
      await loadPositions()
    } catch (err) {
      toast(err.message || '保存标准职位失败')
    }
  }

  const toggleStatus = async (position) => {
    const nextStatus = position.status === 'active' ? 'inactive' : 'active'
    try {
      await updateStandardPosition(position.id, { status: nextStatus })
      toast(nextStatus === 'active' ? '标准职位已启用' : '标准职位已停用')
      await loadPositions()
    } catch (err) {
      toast(err.message || '更新状态失败')
    }
  }

  const resetTagForm = () => {
    setEditingTagId(null)
    setTagForm({
      name: '',
      category: '',
      parentId: '',
      color: '',
      description: '',
      sortOrder: 0,
      status: 'active',
    })
  }

  const editTag = (tag) => {
    setEditingTagId(tag.id)
    setTagForm({
      name: tag.name || '',
      category: tag.category || '',
      parentId: tag.parent_id ? String(tag.parent_id) : '',
      color: tag.color || '',
      description: tag.description || '',
      sortOrder: tag.sort_order || 0,
      status: tag.status || 'active',
    })
  }

  const saveTag = async () => {
    const payload = {
      name: tagForm.name.trim(),
      category: tagForm.category.trim(),
      parent_id: tagForm.parentId ? Number(tagForm.parentId) : null,
      color: tagForm.color.trim() || null,
      description: tagForm.description.trim() || null,
      sort_order: Number(tagForm.sortOrder) || 0,
      status: tagForm.status,
    }
    if (!payload.name || !payload.category) {
      toast('请填写标签名称和分类')
      return
    }

    try {
      if (editingTagId) {
        await updateTagLibraryItem(editingTagId, payload)
        toast('标签已更新')
      } else {
        await createTagLibraryItem(payload)
        toast('标签已新增')
      }
      resetTagForm()
      await loadTags()
    } catch (err) {
      toast(err.message || '保存标签失败')
    }
  }

  const toggleTagStatus = async (tag) => {
    const nextStatus = tag.status === 'active' ? 'inactive' : 'active'
    try {
      await updateTagLibraryItem(tag.id, { status: nextStatus })
      toast(nextStatus === 'active' ? '标签已启用' : '标签已停用')
      await loadTags()
    } catch (err) {
      toast(err.message || '更新标签状态失败')
    }
  }

  const tagNameById = new Map(tags.map(tag => [tag.id, tag.name]))

  const ruleSection = (
    <div className="admin-card" style={{ marginBottom: 20 }}>
      <div className="ac-title row" style={{ justifyContent: 'space-between' }}>
        <span>🎯 人岗匹配规则</span>
        <span className="a-btn sm" style={{ marginLeft: 'auto' }} onClick={() => navigate('/admin-ra/match-rules')}>
          react-admin 规则管理台（试运行） →
        </span>
      </div>
      {ruleLoading ? (
        <div style={{ color: 'var(--a-text-2)', padding: 20 }}>加载匹配规则中...</div>
      ) : ruleConfig ? (
        <table className="admin-table">
          <thead><tr><th>规则名称</th><th>应用范围</th><th>状态</th><th>版本</th><th>维度数</th><th>更新时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr>
              <td>{ruleConfig.name}</td>
              <td>{ruleConfig.scope}</td>
              <td><span className={`a-tag ${ruleConfig.status === 'active' ? 'green' : 'gray'}`}>{ruleConfig.status === 'active' ? '生效中' : ruleConfig.status}</span></td>
              <td>V{ruleConfig.version}</td>
              <td>{ruleConfig.dimensions?.length || 0} 个</td>
              <td>{ruleConfig.updated_at ? new Date(ruleConfig.updated_at).toLocaleString('zh-CN') : '-'}</td>
              <td><span className="a-btn sm" onClick={() => navigate(`/admin/match-rules/${ruleConfig.id}`)}>查看详情</span></td>
            </tr>
          </tbody>
        </table>
      ) : (
        <div style={{ color: 'var(--a-text-2)', padding: 20 }}>暂无匹配规则配置</div>
      )}
    </div>
  )

  const positionsSection = (
    <div className="admin-card">
      <div className="ac-title row" style={{ justifyContent: 'space-between' }}>
        <span>🗂 标准职位库</span>
        <span style={{ color: 'var(--a-text-2)', fontSize: 13 }}>共 {total} 条</span>
      </div>
      <div className="row" style={{ gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
        <input
          value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })}
          placeholder="标准名称"
          style={{ minWidth: 160, flex: '1 1 160px' }}
        />
        <input
          value={form.category}
          onChange={e => setForm({ ...form, category: e.target.value })}
          placeholder="分类"
          style={{ minWidth: 140, flex: '1 1 140px' }}
        />
        <input
          value={form.aliasesText}
          onChange={e => setForm({ ...form, aliasesText: e.target.value })}
          placeholder="别名，用逗号分隔"
          style={{ minWidth: 240, flex: '2 1 240px' }}
        />
        <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}>
          <option value="active">启用</option>
          <option value="inactive">停用</option>
        </select>
        <span className="a-btn sm primary" onClick={savePosition}>{editingId ? '保存' : '新增职位'}</span>
        {editingId && <span className="a-btn sm" onClick={resetForm}>取消</span>}
      </div>
      <textarea
        value={form.description}
        onChange={e => setForm({ ...form, description: e.target.value })}
        placeholder="说明（可选）"
        rows={2}
        style={{ width: '100%', marginBottom: 12, resize: 'vertical' }}
      />
      {error && <div style={{ color: '#dc2626', marginBottom: 12 }}>{error}</div>}
      <table className="admin-table">
        <thead><tr><th>标准名称</th><th>分类</th><th>别名（AI 标准化映射）</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          {loading ? (
            <tr><td colSpan="5" style={{ color: 'var(--a-text-2)' }}>加载标准职位库中...</td></tr>
          ) : positions.length > 0 ? positions.map(position => (
            <tr key={position.id}>
              <td>{position.name}</td>
              <td>{position.category}</td>
              <td style={{ color: 'var(--a-text-2)' }}>{(position.aliases || []).join('、') || '-'}</td>
              <td><span className={`a-tag ${position.status === 'active' ? 'pass' : 'gray'}`}>{position.status === 'active' ? '启用' : '停用'}</span></td>
              <td>
                <span className="a-btn sm" onClick={() => navigate(`/admin/standard-positions/${position.id}`)}>查看详情</span>{' '}
                <span className="a-btn sm" onClick={() => editPosition(position)}>编辑</span>{' '}
                <span className="a-btn sm" onClick={() => toggleStatus(position)}>{position.status === 'active' ? '停用' : '启用'}</span>
              </td>
            </tr>
          )) : (
            <tr><td colSpan="5" style={{ color: 'var(--a-text-2)' }}>暂无标准职位，请新增第一条。</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )

  const tagsSection = (
    <div className="admin-card" style={{ marginTop: section === 'overview' ? 20 : 0 }}>
      <div className="ac-title row" style={{ justifyContent: 'space-between' }}>
        <span>🏷 标签库</span>
        <span style={{ color: 'var(--a-text-2)', fontSize: 13 }}>共 {tagTotal} 条</span>
      </div>
      <div className="row" style={{ gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
        <input
          value={tagForm.name}
          onChange={e => setTagForm({ ...tagForm, name: e.target.value })}
          placeholder="标签名称"
          style={{ minWidth: 140, flex: '1 1 140px' }}
        />
        <input
          value={tagForm.category}
          onChange={e => setTagForm({ ...tagForm, category: e.target.value })}
          placeholder="分类，如 skill / industry"
          style={{ minWidth: 180, flex: '1 1 180px' }}
        />
        <select
          value={tagForm.parentId}
          onChange={e => setTagForm({ ...tagForm, parentId: e.target.value })}
          style={{ minWidth: 160 }}
        >
          <option value="">无父级</option>
          {tags.filter(tag => tag.id !== editingTagId).map(tag => (
            <option key={tag.id} value={tag.id}>{tag.category} / {tag.name}</option>
          ))}
        </select>
        <input
          value={tagForm.color}
          onChange={e => setTagForm({ ...tagForm, color: e.target.value })}
          placeholder="#2563eb"
          style={{ width: 110 }}
        />
        <input
          type="number"
          min="0"
          value={tagForm.sortOrder}
          onChange={e => setTagForm({ ...tagForm, sortOrder: e.target.value })}
          placeholder="排序"
          style={{ width: 90 }}
        />
        <select value={tagForm.status} onChange={e => setTagForm({ ...tagForm, status: e.target.value })}>
          <option value="active">启用</option>
          <option value="inactive">停用</option>
        </select>
        <span className="a-btn sm primary" onClick={saveTag}>{editingTagId ? '保存' : '新增标签'}</span>
        {editingTagId && <span className="a-btn sm" onClick={resetTagForm}>取消</span>}
      </div>
      <textarea
        value={tagForm.description}
        onChange={e => setTagForm({ ...tagForm, description: e.target.value })}
        placeholder="说明（可选）"
        rows={2}
        style={{ width: '100%', marginBottom: 12, resize: 'vertical' }}
      />
      {tagError && <div style={{ color: '#dc2626', marginBottom: 12 }}>{tagError}</div>}
      <table className="admin-table">
        <thead><tr><th>标签</th><th>分类</th><th>父级</th><th>颜色</th><th>排序</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          {tagLoading ? (
            <tr><td colSpan="7" style={{ color: 'var(--a-text-2)' }}>加载标签库中...</td></tr>
          ) : tags.length > 0 ? tags.map(tag => (
            <tr key={tag.id}>
              <td>{tag.name}</td>
              <td>{tag.category}</td>
              <td>{tag.parent_id ? tagNameById.get(tag.parent_id) || tag.parent_id : '-'}</td>
              <td>
                {tag.color ? (
                  <span className="row" style={{ gap: 6 }}>
                    <span style={{ width: 14, height: 14, borderRadius: 4, background: tag.color, display: 'inline-block' }} />
                    {tag.color}
                  </span>
                ) : '-'}
              </td>
              <td>{tag.sort_order}</td>
              <td><span className={`a-tag ${tag.status === 'active' ? 'pass' : 'gray'}`}>{tag.status === 'active' ? '启用' : '停用'}</span></td>
              <td>
                <span className="a-btn sm" onClick={() => navigate(`/admin/tags/${tag.id}`)}>查看详情</span>{' '}
                <span className="a-btn sm" onClick={() => editTag(tag)}>编辑</span>{' '}
                <span className="a-btn sm" onClick={() => toggleTagStatus(tag)}>{tag.status === 'active' ? '停用' : '启用'}</span>
              </td>
            </tr>
          )) : (
            <tr><td colSpan="7" style={{ color: 'var(--a-text-2)' }}>暂无标签，请新增第一条。</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )

  if (section === 'positions') return positionsSection
  if (section === 'tags') return tagsSection
  if (section === 'rules') return ruleSection

  return (
    <>
      <div className="admin-kpis">
        {[
          ['标准职位', loading ? '...' : total, '职位名称标准化与别名映射', 'data-positions'],
          ['标签库', tagLoading ? '...' : tagTotal, '技能、行业、福利等标签层级维护', '/admin/tags'],
          ['匹配规则', ruleLoading ? '...' : (ruleConfig ? `V${ruleConfig.version}` : '-'), '人岗匹配权重与维度配置', 'data-rules'],
          ['操作日志', '审计', '基础数据增删改状态变更留痕', 'data-logs'],
          ['推送队列', '独立管理', '微信真实通知接入前的任务队列', 'data-push'],
        ].map(([label, value, desc, target]) => (
          <div
            key={label}
            className="admin-kpi"
            onClick={() => String(target).startsWith('/') ? navigate(target) : setPage?.(target)}
            style={{ cursor: 'pointer' }}
          >
            <div className="k-label">{label}</div>
            <div className="k-value">{value}</div>
            <div className="k-delta up">{desc}</div>
          </div>
        ))}
      </div>
      {ruleSection}
    </>
  )
}

function BaseDataOperationLogs() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [resourceType, setResourceType] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadLogs = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await listBaseDataOperationLogs({
        limit: 50,
        ...(resourceType ? { resource_type: resourceType } : {}),
      })
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      setItems([])
      setTotal(0)
      setError(err.message || '操作日志加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLogs()
  }, [resourceType])

  const resourceLabel = (value) => ({
    standard_position: '标准职位',
    tag: '标签',
  }[value] || value || '-')

  const actionLabel = (value) => ({
    create: '新增',
    update: '更新',
    deactivate: '停用',
  }[value] || value || '-')

  const summarizeSnapshot = (snapshot) => {
    if (!snapshot) return '-'
    const keys = ['name', 'category', 'status', 'sort_order', 'parent_id']
    const parts = keys
      .filter(key => snapshot[key] !== undefined && snapshot[key] !== null && snapshot[key] !== '')
      .map(key => `${key}: ${Array.isArray(snapshot[key]) ? snapshot[key].join(', ') : snapshot[key]}`)
    return parts.length > 0 ? parts.join('；') : JSON.stringify(snapshot)
  }

  return (
    <div className="admin-card">
      <div className="ac-title row" style={{ justifyContent: 'space-between' }}>
        <span>🧾 基础数据操作日志</span>
        <div className="row" style={{ gap: 8, marginLeft: 'auto' }}>
          {[
            ['', '全部'],
            ['standard_position', '标准职位'],
            ['tag', '标签'],
          ].map(([value, label]) => (
            <button key={value || 'all'} type="button" className={`a-btn sm ${resourceType === value ? 'primary' : ''}`} onClick={() => setResourceType(value)}>
              {label}
            </button>
          ))}
          <button type="button" className="a-btn sm" onClick={loadLogs}>刷新</button>
        </div>
      </div>
      <div className="tiny muted" style={{ marginBottom: 10 }}>
        共 {total} 条；记录标准职位和标签的新增、更新、停用操作。
      </div>
      {error ? (
        <div style={{ color: '#E54545', fontSize: 13 }}>{error}</div>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>资源</th>
              <th>动作</th>
              <th>操作人</th>
              <th>变更前</th>
              <th>变更后</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="7" style={{ color: 'var(--a-text-2)' }}>加载操作日志中...</td></tr>
            ) : items.length > 0 ? items.map(item => (
              <tr key={item.id}>
                <td>{item.id}</td>
                <td>
                  <div>{resourceLabel(item.resource_type)}</div>
                  <div className="tiny muted">#{item.resource_id}</div>
                </td>
                <td><span className="a-tag blue">{actionLabel(item.action)}</span></td>
                <td>{item.actor_id || '-'}</td>
                <td className="tiny muted">{summarizeSnapshot(item.before)}</td>
                <td className="tiny muted">{summarizeSnapshot(item.after)}</td>
                <td>{item.created_at ? new Date(item.created_at).toLocaleString('zh-CN') : '-'}</td>
              </tr>
            )) : (
              <tr><td colSpan="7" style={{ color: 'var(--a-text-2)' }}>暂无操作日志。</td></tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}
