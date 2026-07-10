import React, { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import {
  AIBadge,
  AICard,
  Cell,
  CellGroup,
  EmotionTag,
  FormCell,
  NavBar,
  StatusBadge,
  Switch,
  TabBar,
  useToast,
} from '../components/ui.jsx'
import { pickColor } from '../mock/data.js'
import {
  getCurrentUser,
  getMyCompanyCertification,
  listRecruiterApplications,
  listPublicTagLibraryItems,
  listMyJobs,
  listMyConversations,
  logout,
  searchResumes,
  submitJobForReview,
  updateJob,
  submitCompanyCertification,
  uploadBusinessLicenseForOcr,
  uploadCertificationProofFile,
} from '../services/index.js'
import { applicationStatusTag, applicationStatusText, formatDateTime } from '../utils/applicationView.js'

const leadStatusTagMap = {
  contact_exchanged: 'tag-green',
  contact_needs_review: 'tag-orange',
  contact_waiting: 'tag-blue',
  contact_declined: 'tag-red',
  applied: 'tag-green',
  messaged: 'tag-blue',
  opened: 'tag-gray',
}

function LeadStatusTag({ item }) {
  const status = item?.lead_status || 'opened'
  const label = item?.lead_status_label || '已打开会话'
  return <span className={`tag ${leadStatusTagMap[status] || 'tag-gray'}`} style={{ fontSize: 11, flexShrink: 0 }}>{label}</span>
}

const certStatusMap = {
  not_submitted: { text: '未认证', tag: 'tag-orange', hint: '完成企业认证后可发布岗位' },
  pending: { text: '审核中', tag: 'tag-blue', hint: '认证资料已提交，等待后台审核' },
  approved: { text: '已认证', tag: 'tag-green', hint: '企业认证已通过' },
  rejected: { text: '已驳回', tag: 'tag-red', hint: '请根据驳回原因重新提交' },
}

function getCertMeta(status) {
  return certStatusMap[status] || certStatusMap.not_submitted
}

const verificationMethods = [
  { key: 'business_license', title: '营业执照认证', desc: '上传执照，AI 自动识别企业信息' },
  { key: 'enterprise_email', title: '企业邮箱认证', desc: '使用公司域名邮箱提交人工审核' },
  { key: 'hr_authorization', title: 'HR 授权材料', desc: '上传授权书、工牌或企业通讯工具截图' },
]

export function RecruiterApp() {
  const [searchParams] = useSearchParams()
  const validTabs = new Set(['jobs', 'talent', 'messages', 'profile'])
  const initialTab = validTabs.has(searchParams.get('tab')) ? searchParams.get('tab') : 'jobs'
  const [tab, setTab] = useState(initialTab)
  const navigate = useNavigate()
  const [totalUnread, setTotalUnread] = useState(0)

  useEffect(() => {
    const nextTab = validTabs.has(searchParams.get('tab')) ? searchParams.get('tab') : 'jobs'
    setTab(current => current === nextTab ? current : nextTab)
  }, [searchParams])

  useEffect(() => {
    let alive = true
    listMyConversations({ limit: 100 })
      .then(data => {
        if (!alive) return
        setTotalUnread((data.items || []).reduce((sum, item) => sum + (item.latest_message ? 1 : 0), 0))
      })
      .catch(() => {
        if (alive) setTotalUnread(0)
      })
    return () => { alive = false }
  }, [])

  const handleTabChange = (nextTab) => {
    setTab(nextTab)
    navigate(nextTab === 'jobs' ? '/recruiter/jobs' : `/recruiter/jobs?tab=${nextTab}`, { replace: true })
  }

  const tabs = [
    { key: 'jobs', label: '岗位', icon: '📋' },
    { key: 'talent', label: '人才', icon: '👥' },
    { key: 'messages', label: '消息', icon: '💬', badge: totalUnread || null },
    { key: 'profile', label: '我的', icon: '👤' },
  ]

  return (
    <>
      {tab === 'jobs' && <JobList onCreate={() => navigate('/recruiter/job/create')} />}
      {tab === 'talent' && <RealTalentEntry />}
      {tab === 'messages' && <RealMsgList onOpen={(id) => navigate('/recruiter/chat/' + id)} />}
      {tab === 'profile' && <Profile />}
      <TabBar tabs={tabs} active={tab} onChange={handleTabChange} />
    </>
  )
}

function JobList({ onCreate }) {
  const navigate = useNavigate()
  const toast = useToast()
  const [certification, setCertification] = useState(null)
  const [jobs, setJobs] = useState([])
  const [jobsError, setJobsError] = useState('')
  const [jobsLoading, setJobsLoading] = useState(true)
  const [sortBy, setSortBy] = useState('time')
  const [jobStates, setJobStates] = useState({})
  const [statusFilter, setStatusFilter] = useState('')
  const [submittingJobId, setSubmittingJobId] = useState(null)

  useEffect(() => {
    getMyCompanyCertification()
      .then(setCertification)
      .catch(() => setCertification({ status: 'not_submitted' }))
  }, [])


  const loadJobs = () => {
    setJobsLoading(true)
    return listMyJobs({ limit: 100 })
      .then(data => {
        const mapped = (data.items || []).map(mapApiJobToCard)
        setJobs(mapped)
        setJobsError('')
      })
      .catch(error => {
        setJobs([])
        setJobsError(error.message || '岗位列表加载失败')
      })
      .finally(() => setJobsLoading(false))
  }

  useEffect(() => {
    loadJobs()
  }, [])

  const online = jobs.filter(j => j.status === 'online').length
  const pending = jobs.filter(j => j.status === 'pending').length
  const certMeta = getCertMeta(certification?.status)

  const handleCreate = () => {
    if (certification?.status !== 'approved') {
      toast(certMeta.hint)
      navigate('/recruiter/register')
      return
    }
    onCreate()
  }

  const toggleStatus = (jobId) => {
    setJobStates(state => {
      const next = state[jobId] === 'paused' ? 'active' : 'paused'
      toast(next === 'active' ? '已恢复招聘' : '已暂停招聘')
      return { ...state, [jobId]: next }
    })
  }

  const handleSubmitReview = async (jobId) => {
    if (submittingJobId) return
    try {
      setSubmittingJobId(jobId)
      await submitJobForReview(jobId)
      toast('已提交审核', '✓')
      await loadJobs()
    } catch (error) {
      toast(error.message || '提交审核失败')
    } finally {
      setSubmittingJobId(null)
    }
  }

  let sorted = [...jobs]
  if (statusFilter) sorted = sorted.filter(j => j.status === statusFilter)
  if (sortBy === 'heat') sorted.sort((a, b) => b.views - a.views)
  if (sortBy === 'time') sorted.sort((a, b) => (b.date > a.date ? 1 : -1))

  return (
    <>
      <NavBar title="我的岗位" back={false} right={<span style={{ color: 'var(--wx-green)' }} onClick={handleCreate}>+ 发布</span>} />
      <div className="page has-tabbar">
        {certification?.status !== 'approved' && (
          <div className="ai-tip" style={{ margin: 0, padding: '8px 16px', background: '#FFF7E6', color: 'var(--wx-orange)', fontSize: 12 }}>
            企业认证状态：{certMeta.text}。发布岗位前需要完成企业认证。
            <span style={{ marginLeft: 8, color: 'var(--wx-green)', cursor: 'pointer' }} onClick={() => navigate('/recruiter/register')}>去认证</span>
          </div>
        )}

        <div className="row" style={{ background: '#fff', padding: '16px', gap: 0 }}>
          {[
            ['在线岗位', online, 'online'],
            ['审核中', pending, 'pending'],
            ['本月浏览', jobs.reduce((sum, job) => sum + Number(job.views || 0), 0), ''],
            ['收到留言', jobs.reduce((sum, job) => sum + Number(job.msgs || 0), 0), ''],
          ].map(([label, value, filter]) => (
            <div
              key={label}
              className="grow center"
              style={filter ? { cursor: 'pointer' } : undefined}
              onClick={() => filter && setStatusFilter(statusFilter === filter ? '' : filter)}
            >
              <div style={{ fontSize: 20, fontWeight: 700, color: statusFilter === filter ? 'var(--wx-green)' : 'var(--wx-text)' }}>{value}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{label}{filter && statusFilter === filter ? ' ✓' : ''}</div>
            </div>
          ))}
        </div>

        {statusFilter && (
          <div className="ai-tip center" style={{ fontSize: 12, cursor: 'pointer', padding: '6px 0' }} onClick={() => setStatusFilter('')}>
            已筛选：{statusFilter === 'online' ? '在线岗位' : '审核中'}（{sorted.length} 条），点击取消
          </div>
        )}

        <div className="row between padx" style={{ background: '#fff', padding: '6px 16px', borderTop: '0.5px solid var(--wx-line-light)' }}>
          <div className="row gap6">
            {[
              { key: 'time', label: '按发布时间' },
              { key: 'heat', label: '按热度' },
            ].map(item => (
              <span
                key={item.key}
                className={`tag ${sortBy === item.key ? 'tag-green' : 'tag-gray'}`}
                style={{ cursor: 'pointer', fontSize: 11 }}
                onClick={() => setSortBy(item.key)}
              >
                {item.label}
              </span>
            ))}
          </div>
        </div>

        <div onClick={() => navigate('/recruiter/stats')}>
          <AICard title="AI 数据洞察（点击看详细统计）" tip="AI 分析，仅供参考">
            {jobsLoading ? '正在读取真实岗位数据...' : `「${sorted[0]?.name || '岗位'}」${sorted[0]?.insight || '岗位提交后会先进入审核，通过后再对求职者可见。'}`}
          </AICard>
        </div>

        <div className="cell-group-title row between" style={{ paddingRight: 16 }}>
          <span>待跟进候选人</span>
        </div>
        <div className="cell-group">
          <div className="cell">
            <span className="grow tiny muted">暂无真实待跟进候选人</span>
          </div>
        </div>

        {sorted.map(job => (
          <div key={job.id} className="job-card">
            <div className="jc-top" onClick={() => navigate('/recruiter/jobs/' + job.id, { state: { job } })}>
              <span className="jc-name">{job.name}</span>
              <StatusBadge status={job.status} />
            </div>
            <div className="jc-meta">
              <span className="tag tag-gray">{job.city}</span>
              <span className="tag tag-orange">{job.salary}</span>
              {job.status === 'online' && (
                <span
                  className={`tag ${(jobStates[job.id] || 'active') === 'active' ? 'tag-green' : 'tag-orange'}`}
                  style={{ fontSize: 11, cursor: 'pointer', marginLeft: 6 }}
                  onClick={(event) => { event.stopPropagation(); toggleStatus(job.id) }}
                >
                  {(jobStates[job.id] || 'active') === 'active' ? '积极招聘' : '暂停招聘'}
                </span>
              )}
            </div>
            <div className="jc-company">
              <span style={{ cursor: 'pointer', color: 'var(--wx-blue)' }} onClick={(event) => { event.stopPropagation(); navigate('/recruiter/job/visitors/' + job.id) }}>{job.views} 浏览（{job.uv}人）</span>
              <span style={{ marginLeft: 12, cursor: 'pointer', color: 'var(--wx-blue)' }} onClick={(event) => { event.stopPropagation(); navigate('/recruiter/job/visitors/' + job.id) }}>{job.msgs} 留言</span>
              <span className="grow" />
              <span className="tiny">{job.date}</span>
            </div>
            {job.status !== 'pending' && (
              <div className="row" style={{ borderTop: '0.5px solid var(--wx-line-light)', marginTop: 10, paddingTop: 10, gap: 8 }}>
                <button className="btn btn-weak btn-sm" onClick={() => navigate('/recruiter/job-portrait')}>岗位画像</button>
                <button className="btn btn-default btn-sm" onClick={() => navigate('/recruiter/stats')}>数据统计</button>
                {job.status === 'online' && (
                  <button className="btn btn-weak btn-sm" onClick={() => toggleStatus(job.id)} style={{ marginLeft: 'auto' }}>
                    {(jobStates[job.id] || 'active') === 'active' ? '暂停' : '恢复'}
                  </button>
                )}
                {['draft', 'rejected'].includes(job.status) && (
                  <button
                    className={`btn btn-primary btn-sm ${submittingJobId === job.id ? 'btn-disabled' : ''}`}
                    disabled={submittingJobId === job.id}
                    onClick={(event) => {
                      event.stopPropagation()
                      handleSubmitReview(job.id)
                    }}
                    style={{ marginLeft: 'auto' }}
                  >
                    {submittingJobId === job.id ? '提交中...' : '提交审核'}
                  </button>
                )}
              </div>
            )}
          </div>
        ))}

        <div className="btn-block-wrap row gap12">
          <button className="btn btn-default" style={{ flex: '0 0 130px' }} onClick={() => navigate('/recruiter/job/upload')}>批量导入</button>
          <button className="btn btn-primary" onClick={handleCreate}>发布新岗位</button>
        </div>
      </div>
    </>
  )
}

function mapApiJobToCard(job) {
  return {
    id: job.id,
    name: job.title,
    city: job.city,
    salary: `${job.salary_min}K-${job.salary_max}K`,
    status: job.status === 'active' ? 'online' : job.status,
    apiStatus: job.status,
    experience: job.experience,
    education: job.education,
    description: job.description,
    requirement: job.requirement,
    benefits: job.benefits,
    tags: job.tags || [],
    tagRefs: job.tag_refs || [],
    companyDisplayMode: job.company_display_mode || 'display_name',
    contactPhonePublic: Boolean(job.contact_phone_public),
    contactEmailPublic: Boolean(job.contact_email_public),
    contactWechatPublic: Boolean(job.contact_wechat_public),
    publicContact: job.public_contact || {},
    rejectReason: job.reject_reason,
    reviewedAt: job.reviewed_at,
    publishedAt: job.published_at,
    views: job.view_count || 0,
    uv: 0,
    msgs: job.conversation_count || 0,
    date: job.created_at ? new Date(job.created_at).toLocaleDateString('zh-CN') : '',
    insight: job.status === 'pending'
      ? '已提交审核，审核通过后会对求职者可见。'
      : job.status === 'draft'
        ? '岗位草稿已保存，提交审核后才会对求职者可见。'
        : job.status === 'rejected'
          ? '岗位已被驳回，请根据原因调整后重新提交审核。'
          : '岗位已通过审核，可继续观察浏览与留言数据。',
  }
}

const jobDetailStatus = {
  online: { text: '已上线', tag: 'tag-green' },
  active: { text: '已上线', tag: 'tag-green' },
  pending: { text: '审核中', tag: 'tag-blue' },
  draft: { text: '草稿', tag: 'tag-gray' },
  closed: { text: '已关闭', tag: 'tag-gray' },
  rejected: { text: '已驳回', tag: 'tag-red' },
}

function normalizeJobDetail(job) {
  if (!job) return null
  return job.name ? job : mapApiJobToCard(job)
}

export function RecruiterJobDetail() {
  const { jobId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const toast = useToast()
  const [job, setJob] = useState(normalizeJobDetail(location.state?.job))
  const [loading, setLoading] = useState(!location.state?.job)
  const [error, setError] = useState('')
  const [submittingReview, setSubmittingReview] = useState(false)
  const [savingVisibility, setSavingVisibility] = useState(false)
  const [visibility, setVisibility] = useState({
    company_display_mode: 'display_name',
    contact_phone_public: false,
    contact_email_public: false,
    contact_wechat_public: false,
  })

  useEffect(() => {
    if (job) return
    setLoading(true)
    listMyJobs({ limit: 100 })
      .then(data => {
        const found = (data.items || []).find(item => String(item.id) === String(jobId))
        if (!found) {
          setError('未找到该岗位，可能不是当前招聘者发布的岗位。')
          return
        }
        setJob(normalizeJobDetail(found))
        setError('')
      })
      .catch(err => setError(err.message || '岗位详情加载失败'))
      .finally(() => setLoading(false))
  }, [job, jobId])

  useEffect(() => {
    if (!job) return
    setVisibility({
      company_display_mode: job.companyDisplayMode || 'display_name',
      contact_phone_public: Boolean(job.contactPhonePublic),
      contact_email_public: Boolean(job.contactEmailPublic),
      contact_wechat_public: Boolean(job.contactWechatPublic),
    })
  }, [job?.id, job?.companyDisplayMode, job?.contactPhonePublic, job?.contactEmailPublic, job?.contactWechatPublic])

  const meta = jobDetailStatus[job?.status] || jobDetailStatus[job?.apiStatus] || { text: job?.status || '未知', tag: 'tag-gray' }
  const tagList = Array.isArray(job?.tagRefs) && job.tagRefs.length > 0
    ? job.tagRefs.map(tag => tag.name).filter(Boolean)
    : Array.isArray(job?.tags) ? job.tags : []
  const canSubmitReview = ['draft', 'rejected'].includes(job?.status)
  const setVisibilityField = (key, value) => setVisibility(current => ({ ...current, [key]: value }))

  const handleDetailSubmitReview = async () => {
    if (!job || submittingReview) return
    try {
      setSubmittingReview(true)
      const updated = await submitJobForReview(job.id)
      setJob(normalizeJobDetail(updated))
      toast('已提交审核', '✓')
    } catch (err) {
      toast(err.message || '提交审核失败')
    } finally {
      setSubmittingReview(false)
    }
  }

  const handleSaveVisibility = async () => {
    if (!job || savingVisibility) return
    try {
      setSavingVisibility(true)
      const updated = await updateJob(job.id, visibility)
      setJob(normalizeJobDetail(updated))
      toast('公开设置已保存', '✓')
    } catch (err) {
      toast(err.message || '保存公开设置失败')
    } finally {
      setSavingVisibility(false)
    }
  }

  return (
    <>
      <NavBar title="岗位详情" />
      <div className="page">
        {loading && (
          <div className="empty" style={{ padding: '60px 20px' }}>
            <div className="tiny muted">正在加载岗位详情...</div>
          </div>
        )}

        {!loading && error && (
          <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>
        )}

        {!loading && job && (
          <>
            <div className="job-card">
              <div className="row between" style={{ alignItems: 'flex-start', gap: 12 }}>
                <div className="grow" style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 18, fontWeight: 700, lineHeight: 1.35 }}>{job.name}</div>
                  <div className="row gap6" style={{ marginTop: 8, flexWrap: 'wrap' }}>
                    <span className={`tag ${meta.tag}`}>{meta.text}</span>
                    <span className="tag tag-gray">{job.city || '城市未填'}</span>
                    <span className="tag tag-orange">{job.salary || '薪资未填'}</span>
                  </div>
                </div>
              </div>
              {job.rejectReason && (
                <div className="ai-tip" style={{ marginTop: 10, color: 'var(--wx-red)' }}>
                  驳回原因：{job.rejectReason}
                </div>
              )}
            </div>

            <div className="cell-group-title">岗位要求</div>
            <CellGroup>
              <Cell label="经验要求" value={job.experience || '未填写'} />
              <Cell label="学历要求" value={job.education || '未填写'} />
              <Cell label="发布时间" value={job.date || '未记录'} />
            </CellGroup>

            <div className="cell-group-title">公开设置</div>
            <CellGroup>
              <div className="cell">
                <span className="cell-label">企业名称展示</span>
                <select
                  value={visibility.company_display_mode}
                  onChange={event => setVisibilityField('company_display_mode', event.target.value)}
                  style={{ border: 0, background: 'transparent', textAlign: 'right', color: 'var(--wx-text-2)', fontSize: 14 }}
                >
                  <option value="company_name">企业真名</option>
                  <option value="display_name">招聘者昵称</option>
                  <option value="anonymous">匿名企业</option>
                </select>
              </div>
              {[
                ['contact_email_public', '企业邮箱'],
                ['contact_phone_public', '联系电话'],
                ['contact_wechat_public', '微信'],
              ].map(([key, label]) => (
                <div className="cell" key={key}>
                  <span className="cell-label">{label}</span>
                  <Switch on={visibility[key]} onClick={() => setVisibilityField(key, !visibility[key])} />
                </div>
              ))}
              <div style={{ padding: '10px 16px', display: 'flex', gap: 8, alignItems: 'center' }}>
                <span className="tiny muted grow">
                  仅修改公开设置不会让已上线岗位重新进入审核。
                </span>
                <button className={`btn btn-weak btn-sm ${savingVisibility ? 'btn-disabled' : ''}`} disabled={savingVisibility} onClick={handleSaveVisibility}>
                  {savingVisibility ? '保存中...' : '保存'}
                </button>
              </div>
            </CellGroup>

            <div className="cell-group-title">岗位职责</div>
            <div className="cell-group">
              <div style={{ padding: '12px 16px', fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                {job.description || job.insight || '暂无岗位职责'}
              </div>
            </div>

            <div className="cell-group-title">任职要求</div>
            <div className="cell-group">
              <div style={{ padding: '12px 16px', fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                {job.requirement || '暂无任职要求'}
              </div>
            </div>

            {job.benefits && (
              <>
                <div className="cell-group-title">福利待遇</div>
                <div className="cell-group">
                  <div style={{ padding: '12px 16px', fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{job.benefits}</div>
                </div>
              </>
            )}

            {tagList.length > 0 && (
              <>
                <div className="cell-group-title">岗位标签</div>
                <div className="cell-group">
                  <div className="tagcloud" style={{ padding: '12px 16px' }}>
                    {tagList.map(tag => <span key={tag} className="tag tag-green">{tag}</span>)}
                  </div>
                </div>
              </>
            )}

            <div className="btn-block-wrap row gap12">
              <button className="btn btn-default" onClick={() => navigate('/recruiter/jobs')}>返回岗位列表</button>
              {canSubmitReview ? (
                <button className={`btn btn-primary ${submittingReview ? 'btn-disabled' : ''}`} disabled={submittingReview} onClick={handleDetailSubmitReview}>
                  {submittingReview ? '提交中...' : '提交审核'}
                </button>
              ) : (
                <button className="btn btn-primary" onClick={() => navigate('/recruiter/talent')}>查看投递</button>
              )}
            </div>
          </>
        )}
      </div>
    </>
  )
}

function RealMsgList({ onOpen }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    setLoading(true)
    listMyConversations({ limit: 100 })
      .then(data => {
        if (!alive) return
        setItems(data.items || [])
      })
      .catch(() => {
        if (alive) setItems([])
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => { alive = false }
  }, [])

  return (
    <>
      <NavBar title="消息" back={false} />
      <div className="page has-tabbar" style={{ background: '#fff' }}>
        {loading && <div className="ai-tip" style={{ margin: 16 }}>正在加载消息...</div>}
        {!loading && items.length === 0 && <div className="ai-tip" style={{ margin: 16 }}>还没有真实会话</div>}
        {!loading && items.map(chat => (
          <div key={chat.id} className="cell link" onClick={() => onOpen(chat.id)} style={{ alignItems: 'flex-start', padding: '12px 16px' }}>
            <span className="msg-avatar avatar" style={{ width: 46, height: 46, borderRadius: 6, background: pickColor(chat.seeker_id || 0), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 17, fontWeight: 600, marginRight: 12, flexShrink: 0 }}>
              {(chat.seeker_display_name || '求')[0]}
            </span>
            <div className="grow" style={{ overflow: 'hidden' }}>
              <div className="row between">
                <span style={{ fontWeight: 500 }}>{chat.seeker_display_name || '求职者'}</span>
                <span className="tiny muted">{chat.last_message_at ? new Date(chat.last_message_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''}</span>
              </div>
              <div className="row" style={{ marginTop: 3, gap: 6 }}>
                <LeadStatusTag item={chat} />
                <EmotionTag level={chat.contact_exchange?.status === 'accepted' ? 'positive' : 'neutral'} />
                <span className="tiny muted" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{chat.latest_message?.content || '暂无消息'}</span>
              </div>
              <div className="tiny" style={{ color: 'var(--wx-text-light)', marginTop: 3 }}>应聘岗位：{chat.job_title || `#${chat.job_id}`}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

function Profile() {
  const navigate = useNavigate()
  const currentUser = getCurrentUser()
  const companyName = currentUser?.display_name || '企业账号'
  const companyInitial = companyName.trim().charAt(0) || '企'
  const [certification, setCertification] = useState(null)
  const [profileStats, setProfileStats] = useState({
    jobs: '读取中',
    talent: '读取中',
    interviews: '待接入',
    analysis: '待接入',
    notifications: '待接入',
  })
  const certMeta = getCertMeta(certification?.status)

  useEffect(() => {
    getMyCompanyCertification()
      .then(setCertification)
      .catch(() => setCertification({ status: 'not_submitted' }))
  }, [])

  useEffect(() => {
    let alive = true
    Promise.allSettled([
      listMyJobs({ limit: 100 }),
      listRecruiterApplications({ limit: 100 }),
    ]).then(([jobsResult, applicationsResult]) => {
      if (!alive) return
      const jobItems = jobsResult.status === 'fulfilled' ? (jobsResult.value.items || []) : []
      const applicationItems = applicationsResult.status === 'fulfilled' ? (applicationsResult.value.items || []) : []
      const online = jobItems.filter(item => ['active', 'online'].includes(item.status)).length
      const pending = jobItems.filter(item => item.status === 'pending').length
      setProfileStats({
        jobs: `${online} 在线 · ${pending} 审核中`,
        talent: `${applicationItems.length} 人`,
        interviews: '待接入',
        analysis: applicationItems.length ? `${applicationItems.length} 人` : '暂无',
        notifications: '待接入',
      })
    })
    return () => { alive = false }
  }, [])

  return (
    <>
      <NavBar title="我的" back={false} />
      <div className="page has-tabbar">
        <div className="row" style={{ background: '#fff', padding: '20px 16px', gap: 14 }}>
          <span style={{ width: 56, height: 56, borderRadius: 8, background: 'var(--wx-green-bg)', color: 'var(--wx-green-dark)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, fontWeight: 700 }}>{companyInitial}</span>
          <div className="grow">
            <div style={{ fontSize: 17, fontWeight: 600 }}>{companyName}</div>
            <div className="row gap6" style={{ marginTop: 4 }}>
              <span className={`tag ${certMeta.tag}`}>{certMeta.text}</span>
              <span className="tag tag-blue">优质招聘者</span>
            </div>
            {certification?.status === 'rejected' && certification.reject_reason && (
              <div className="tiny" style={{ marginTop: 6, color: 'var(--wx-red)' }}>驳回原因：{certification.reject_reason}</div>
            )}
          </div>
        </div>

        <CellGroup>
          <Cell icon="📋" iconBg="#ECF9F1" label="我的岗位" value={profileStats.jobs} link onClick={() => navigate('/recruiter/jobs?tab=jobs')} />
          <Cell icon="👥" iconBg="#E8F5FF" label="人才池" value={profileStats.talent} link onClick={() => navigate('/recruiter/talent')} />
          <Cell icon="📅" iconBg="#FFF3E6" label="面试管理" value={profileStats.interviews} link onClick={() => navigate('/recruiter/interviews')} />
          <Cell icon="📊" iconBg="#FFF3E6" label="候选人分析" value={profileStats.analysis} link onClick={() => navigate('/recruiter/candidate')} />
          <Cell icon="🏢" iconBg="#E8F5FF" label="企业画像" value="AI 生成" link onClick={() => navigate('/recruiter/company-portrait')} />
          <Cell icon="📈" iconBg="#E8F5FF" label="数据统计" link onClick={() => navigate('/recruiter/stats')} />
          <Cell icon="✓" iconBg="#FFF3E6" label="企业认证" value={certMeta.text} link onClick={() => navigate('/recruiter/register')} />
        </CellGroup>
        <CellGroup>
          <Cell icon="🔔" iconBg="#FFE6E6" label="通知中心" value={profileStats.notifications} link onClick={() => navigate('/recruiter/notifications')} />
          <Cell icon="💬" iconBg="#ECF9F1" label="智能客服" link onClick={() => navigate('/support')} />
          <Cell icon="🛡" iconBg="#E8F5FF" label="隐私与公开设置" link />
          <Cell icon="⚙" iconBg="#F2F2F2" label="账号设置" link />
        </CellGroup>
        <div className="btn-block-wrap"><button className="btn btn-default" onClick={logout}>退出登录</button></div>
      </div>
    </>
  )
}

function RealTalentEntry() {
  const navigate = useNavigate()
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tagOptions, setTagOptions] = useState([])
  const [selectedTagId, setSelectedTagId] = useState('')
  const [resumeResults, setResumeResults] = useState([])
  const [resumeSearchLoading, setResumeSearchLoading] = useState(false)

  useEffect(() => {
    let alive = true
    setLoading(true)
    listRecruiterApplications({ limit: 100 })
      .then(data => {
        if (!alive) return
        setApplications(data.items || [])
        setError('')
      })
      .catch(err => {
        if (!alive) return
        setApplications([])
        setError(err.message || 'Applications load failed')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    let alive = true
    listPublicTagLibraryItems({ limit: 100 })
      .then(data => {
        if (alive) setTagOptions(data.items || [])
      })
      .catch(() => {
        if (alive) setTagOptions([])
      })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    if (!selectedTagId) {
      setResumeResults([])
      return undefined
    }
    const selectedTag = tagOptions.find(item => String(item.id) === String(selectedTagId))
    let alive = true
    setResumeSearchLoading(true)
    searchResumes({ q: selectedTag?.name || '候选人', tag_id: selectedTagId, limit: 20 })
      .then(data => {
        if (alive) setResumeResults(data.items || [])
      })
      .catch(() => {
        if (alive) setResumeResults([])
      })
      .finally(() => {
        if (alive) setResumeSearchLoading(false)
      })
    return () => { alive = false }
  }, [selectedTagId, tagOptions])

  const recent = applications.slice(0, 5)
  const newCount = applications.filter(item => item.status === 'submitted').length
  const activeCount = applications.filter(item => ['viewed', 'interview_invited'].includes(item.status)).length
  const hiredCount = applications.filter(item => item.status === 'hired').length

  return (
    <>
      <NavBar title="人才池" back={false} right={<span style={{ color: 'var(--wx-green)' }} onClick={() => navigate('/recruiter/talent')}>查看全部 ›</span>} />
      <div className="page has-tabbar">
        <div className="row" style={{ background: '#fff', padding: '16px', gap: 0 }}>
          {[
            ['Total', applications.length],
            ['New', newCount],
            ['Active', activeCount],
            ['Hired', hiredCount],
          ].map(([label, value]) => (
            <div key={label} className="grow center">
              <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{label}</div>
            </div>
          ))}
        </div>

        <div className="cell-group-title">候选人标签</div>
        <div className="cell-group">
          <div style={{ padding: '12px 16px' }}>
            <div className="row gap6" style={{ flexWrap: 'wrap' }}>
              <span
                className={`tag ${selectedTagId ? 'tag-gray' : 'tag-green'}`}
                style={{ cursor: 'pointer', fontSize: 12 }}
                onClick={() => setSelectedTagId('')}
              >
                全部标签
              </span>
              {tagOptions.slice(0, 10).map(item => (
                <span
                  key={item.id}
                  className={`tag ${String(selectedTagId) === String(item.id) ? 'tag-green' : 'tag-gray'}`}
                  style={{ cursor: 'pointer', fontSize: 12 }}
                  onClick={() => setSelectedTagId(String(item.id))}
                >
                  {item.name}
                </span>
              ))}
            </div>
          </div>
        </div>

        {selectedTagId && (
          <>
            <div className="cell-group-title">标签匹配候选人</div>
            <div className="cell-group">
              {resumeSearchLoading && (
                <div className="cell"><span className="grow tiny muted">正在搜索候选人...</span></div>
              )}
              {!resumeSearchLoading && resumeResults.slice(0, 3).map(item => (
                <div key={item.structured_profile_id || item.seeker_id} className="cell">
                  <span className="avatar" style={{ width: 36, height: 36, borderRadius: 6, background: pickColor(item.seeker_id), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 600, marginRight: 10, flexShrink: 0 }}>{(item.real_name || item.seeker_display_name || 'C')[0]}</span>
                  <div className="grow" style={{ minWidth: 0 }}>
                    <div className="row between" style={{ gap: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.real_name || item.seeker_display_name || `Candidate #${item.seeker_id}`}</span>
                      <span className="tag tag-blue" style={{ fontSize: 11, flexShrink: 0 }}>{Math.round(item.score || 0)} 分</span>
                    </div>
                    <div className="tiny muted" style={{ marginTop: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {[item.target_position, item.current_city, (item.tag_refs || []).map(tag => tag.name).join('、')].filter(Boolean).join(' · ')}
                    </div>
                  </div>
                </div>
              ))}
              {!resumeSearchLoading && resumeResults.length === 0 && (
                <div className="cell"><span className="grow tiny muted">暂无匹配该标签的候选人。</span></div>
              )}
            </div>
          </>
        )}

        <div className="cell-group-title">Recent applications</div>
        {loading && <div className="ai-tip" style={{ margin: 16 }}>Loading applications...</div>}
        {error && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>}
        <div className="cell-group">
          {!loading && !error && recent.map(item => (
            <div key={item.id} className="cell link" onClick={() => navigate('/recruiter/applications/' + item.id, { state: { application: item } })}>
              <span className="avatar" style={{ width: 36, height: 36, borderRadius: 6, background: pickColor(item.seeker_id || item.id), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 600, marginRight: 10, flexShrink: 0 }}>{(item.seeker_display_name || 'C')[0]}</span>
              <div className="grow" style={{ minWidth: 0 }}>
                <div className="row between" style={{ gap: 8 }}>
                  <span style={{ fontSize: 14, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.seeker_display_name || `Candidate #${item.seeker_id}`}</span>
                  <span className={`tag ${applicationStatusTag[item.status] || 'tag-gray'}`} style={{ fontSize: 11, flexShrink: 0 }}>{applicationStatusText[item.status] || item.status}</span>
                </div>
                <div className="tiny muted" style={{ marginTop: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {item.job_title || `Job #${item.job_id}`} · {formatDateTime(item.created_at)}
                </div>
              </div>
              <span className="cell-arrow">›</span>
            </div>
          ))}
          {!loading && !error && recent.length === 0 && (
            <div className="cell">
              <span className="grow tiny muted">No real applications yet.</span>
            </div>
          )}
        </div>

        <div className="btn-block-wrap">
          <button className="btn btn-primary" onClick={() => navigate('/recruiter/talent')}>进入完整人才池</button>
        </div>
      </div>
    </>
  )
}

export function RecruiterRegister() {
  const navigate = useNavigate()
  const toast = useToast()
  const fileInputRef = useRef(null)
  const proofInputRef = useRef(null)
  const [ocrDone, setOcrDone] = useState(false)
  const [ocrLoading, setOcrLoading] = useState(false)
  const [proofUploading, setProofUploading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [certification, setCertification] = useState(null)
  const [license, setLicense] = useState(null)
  const [proof, setProof] = useState(null)
  const [verificationMethod, setVerificationMethod] = useState('business_license')
  const [form, setForm] = useState({
    company: '',
    credit: '',
    legal: '',
    address: '',
    workEmail: '',
    applicantName: '',
    applicantTitle: '',
    applicantPhone: '',
    applicantWechat: '',
    note: '',
    virtual: '',
  })
  const certMeta = getCertMeta(certification?.status)

  useEffect(() => {
    getMyCompanyCertification()
      .then(data => {
        setCertification(data)
        setVerificationMethod(data.verification_method || 'business_license')
        if (data.company_name) {
          setForm({
            company: data.company_name || '',
            credit: data.unified_social_credit_code || '',
            legal: data.legal_representative || '',
            address: data.registered_address || '',
            workEmail: data.work_email || '',
            applicantName: data.applicant_name || '',
            applicantTitle: data.applicant_title || '',
            applicantPhone: data.applicant_phone || '',
            applicantWechat: data.applicant_wechat || '',
            note: data.verification_note || '',
            virtual: '',
          })
          if (data.license_file_name || data.license_file_url) {
            setLicense({
              license_file_name: data.license_file_name,
              license_file_url: data.license_file_url,
            })
          }
          if (data.proof_file_name || data.proof_file_url) {
            setProof({
              proof_file_name: data.proof_file_name,
              proof_file_url: data.proof_file_url,
            })
          }
          setOcrDone(Boolean(data.license_file_name || data.license_file_url))
        }
      })
      .catch(() => setCertification({ status: 'not_submitted' }))
  }, [])

  const runOcr = () => {
    if (!ocrLoading) fileInputRef.current?.click()
  }

  const uploadProof = () => {
    if (!proofUploading) proofInputRef.current?.click()
  }

  const handleLicenseChange = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    try {
      setOcrLoading(true)
      const data = await uploadBusinessLicenseForOcr(file)
      setForm(prev => ({
        ...prev,
        company: data.company_name || prev.company,
        credit: data.unified_social_credit_code || prev.credit,
        legal: data.legal_representative || prev.legal,
        address: data.registered_address || prev.address,
      }))
      setLicense(data)
      setOcrDone(true)
      toast('营业执照识别完成', '✓')
    } catch (error) {
      toast(error.message || '营业执照识别失败')
    } finally {
      setOcrLoading(false)
    }
  }

  const handleProofChange = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    try {
      setProofUploading(true)
      const data = await uploadCertificationProofFile(file)
      setProof(data)
      toast('证明材料已上传', '✓')
    } catch (error) {
      toast(error.message || '证明材料上传失败')
    } finally {
      setProofUploading(false)
    }
  }

  const handleSubmit = async () => {
    if (!form.company.trim()) {
      toast('请填写企业名称')
      return
    }

    const normalizedCredit = form.credit.trim().toUpperCase()
    if (verificationMethod === 'business_license') {
      if (!normalizedCredit || !form.legal.trim() || !form.address.trim()) {
        toast('请填写完整营业执照认证信息')
        return
      }
      if (!/^[0-9A-Z]{18}$/.test(normalizedCredit)) {
        toast('统一社会信用代码必须是18位数字或大写字母')
        return
      }
    }

    if (verificationMethod === 'enterprise_email' && !form.workEmail.trim()) {
      toast('请填写企业邮箱')
      return
    }

    if (verificationMethod === 'hr_authorization' && !(proof?.proof_file_url || certification?.proof_file_url)) {
      toast('请上传授权书、工牌或企业通讯工具截图')
      return
    }

    try {
      setLoading(true)
      const response = await submitCompanyCertification({
        verification_method: verificationMethod,
        company_name: form.company.trim(),
        unified_social_credit_code: normalizedCredit || null,
        legal_representative: form.legal.trim() || null,
        registered_address: form.address.trim() || null,
        license_file_url: verificationMethod === 'business_license'
          ? license?.license_file_url || certification?.license_file_url || null
          : null,
        license_file_name: verificationMethod === 'business_license'
          ? license?.license_file_name || certification?.license_file_name || null
          : null,
        proof_file_url: verificationMethod === 'hr_authorization'
          ? proof?.proof_file_url || certification?.proof_file_url || null
          : null,
        proof_file_name: verificationMethod === 'hr_authorization'
          ? proof?.proof_file_name || certification?.proof_file_name || null
          : null,
        work_email: form.workEmail.trim() || null,
        applicant_name: form.applicantName.trim() || null,
        applicant_title: form.applicantTitle.trim() || null,
        applicant_phone: form.applicantPhone.trim() || null,
        applicant_wechat: form.applicantWechat.trim() || null,
        verification_note: form.note.trim() || null,
      })
      setCertification(response)
      toast('企业认证已提交，等待审核', '✓')
      setTimeout(() => navigate('/recruiter/jobs'), 800)
    } catch (error) {
      toast(error.message || '提交失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <NavBar title="企业注册认证" onBack={() => navigate('/')} />
      <div className="page" style={{ paddingBottom: 90 }}>
        <div style={{ background: '#fff', padding: '14px 16px', borderBottom: '8px solid var(--wx-bg)' }}>
          <div className="row between">
            <div>
              <div style={{ fontWeight: 600 }}>认证状态</div>
              <div className="tiny muted" style={{ marginTop: 3 }}>{certMeta.hint}</div>
            </div>
            <span className={`tag ${certMeta.tag}`}>{certMeta.text}</span>
          </div>
          {certification?.status === 'rejected' && certification.reject_reason && (
            <div className="tiny" style={{ marginTop: 10, color: 'var(--wx-red)', background: '#FFF0F0', padding: '8px 10px', borderRadius: 6 }}>
              驳回原因：{certification.reject_reason}
            </div>
          )}
        </div>

        <div className="cell-group-title">认证方式</div>
        <div className="cell-group">
          <div style={{ padding: 12, display: 'grid', gap: 10 }}>
            {verificationMethods.map(method => (
              <div
                key={method.key}
                className={`opt-card ${verificationMethod === method.key ? 'sel' : ''}`}
                style={{ cursor: 'pointer' }}
                onClick={() => setVerificationMethod(method.key)}
              >
                <div className="row between">
                  <span style={{ fontWeight: 600 }}>{method.title}</span>
                  {verificationMethod === method.key && <span className="tag tag-green">当前</span>}
                </div>
                <div className="tiny muted" style={{ marginTop: 4 }}>{method.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {verificationMethod === 'business_license' && (
          <>
            <div className="cell-group-title">营业执照</div>
            <div className="cell-group">
              <div style={{ padding: 16 }}>
                <input ref={fileInputRef} type="file" accept=".jpg,.jpeg,.png,.webp,.bmp,.heic,.heif,.pdf,image/*" style={{ display: 'none' }} onChange={handleLicenseChange} />
                <div onClick={runOcr}
                  style={{ border: '1px dashed var(--wx-line)', borderRadius: 10, minHeight: 150, padding: '18px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8, background: ocrDone ? 'var(--ai-bg)' : '#FAFAFA', color: 'var(--wx-text-gray)', cursor: ocrLoading ? 'default' : 'pointer', textAlign: 'center' }}>
                  {ocrLoading ? (
                    <><span className="spin" style={{ width: 22, height: 22 }} /><span style={{ fontSize: 13 }}>AI 正在识别营业执照...</span></>
                  ) : ocrDone ? (
                    <>
                      <span style={{ fontSize: 32 }}>📄</span>
                      <span style={{ fontSize: 13, color: 'var(--wx-green-dark)' }}>✓ 营业执照已上传并识别</span>
                      {license?.license_file_name && <span className="tiny muted">{license.license_file_name}</span>}
                      {license?.confidence && <span className="tag tag-blue" style={{ fontSize: 11 }}>OCR {Math.round(license.confidence * 100)}%</span>}
                      <span className="tiny" style={{ color: 'var(--wx-green)' }}>点击重新上传</span>
                    </>
                  ) : (
                    <>
                      <span style={{ fontSize: 32 }}>+</span>
                      <span style={{ fontSize: 13 }}>上传营业执照，AI 自动识别填充</span>
                      <AIBadge soft>AI OCR</AIBadge>
                    </>
                  )}
                </div>
              </div>
            </div>

            {ocrDone && <div className="ai-tip padx" style={{ marginTop: -4 }}>以下带「AI识别」标记的字段由 OCR 自动填充，请核对后确认或修改</div>}
          </>
        )}

        {verificationMethod === 'hr_authorization' && (
          <>
            <div className="cell-group-title">证明材料</div>
            <div className="cell-group">
              <div style={{ padding: 16 }}>
                <input ref={proofInputRef} type="file" accept=".jpg,.jpeg,.png,.webp,.bmp,.heic,.heif,.pdf,image/*" style={{ display: 'none' }} onChange={handleProofChange} />
                <div onClick={uploadProof}
                  style={{ border: '1px dashed var(--wx-line)', borderRadius: 10, minHeight: 128, padding: '18px 12px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8, background: proof ? 'var(--ai-bg)' : '#FAFAFA', color: 'var(--wx-text-gray)', cursor: proofUploading ? 'default' : 'pointer', textAlign: 'center' }}>
                  {proofUploading ? (
                    <><span className="spin" style={{ width: 22, height: 22 }} /><span style={{ fontSize: 13 }}>正在上传证明材料...</span></>
                  ) : proof ? (
                    <>
                      <span style={{ fontSize: 30 }}>📎</span>
                      <span style={{ fontSize: 13, color: 'var(--wx-green-dark)' }}>✓ 证明材料已上传</span>
                      <span className="tiny muted">{proof.proof_file_name}</span>
                      <span className="tiny" style={{ color: 'var(--wx-green)' }}>点击重新上传</span>
                    </>
                  ) : (
                    <>
                      <span style={{ fontSize: 32 }}>+</span>
                      <span style={{ fontSize: 13 }}>上传授权书、工牌或企业通讯工具截图</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        <div className="cell-group-title">企业信息</div>
        <div className="cell-group">
          <FormCell label="企业名称" req>
            <input value={form.company} placeholder="请输入企业全称" onChange={event => setForm(prev => ({ ...prev, company: event.target.value }))} />
            {ocrDone && form.company && <span className="ai-badge soft" style={{ marginTop: 4 }}>AI识别</span>}
          </FormCell>
          {verificationMethod === 'business_license' && (
            <>
              <FormCell label="信用代码" req>
                <input value={form.credit} placeholder="统一社会信用代码" onChange={event => setForm(prev => ({ ...prev, credit: event.target.value }))} />
                {ocrDone && form.credit && <span className="ai-badge soft" style={{ marginTop: 4 }}>AI识别</span>}
              </FormCell>
              <FormCell label="法定代表人" req>
                <input value={form.legal} placeholder="法人姓名" onChange={event => setForm(prev => ({ ...prev, legal: event.target.value }))} />
                {ocrDone && form.legal && <span className="ai-badge soft" style={{ marginTop: 4 }}>AI识别</span>}
              </FormCell>
              <FormCell label="注册地址" req>
                <input value={form.address} placeholder="企业注册地址" onChange={event => setForm(prev => ({ ...prev, address: event.target.value }))} />
              </FormCell>
            </>
          )}
          {(verificationMethod === 'enterprise_email' || verificationMethod === 'hr_authorization') && (
            <>
              <FormCell label="企业邮箱" req={verificationMethod === 'enterprise_email'}>
                <input value={form.workEmail} placeholder="name@company.com" onChange={event => setForm(prev => ({ ...prev, workEmail: event.target.value }))} />
              </FormCell>
              <FormCell label="申请人">
                <input value={form.applicantName} placeholder="HR 或招聘负责人姓名" onChange={event => setForm(prev => ({ ...prev, applicantName: event.target.value }))} />
              </FormCell>
              <FormCell label="职位">
                <input value={form.applicantTitle} placeholder="例如 HRBP、招聘经理" onChange={event => setForm(prev => ({ ...prev, applicantTitle: event.target.value }))} />
              </FormCell>
              <FormCell label="联系电话">
                <input value={form.applicantPhone} placeholder="便于管理员核验" onChange={event => setForm(prev => ({ ...prev, applicantPhone: event.target.value }))} />
              </FormCell>
              <FormCell label="微信">
                <input value={form.applicantWechat} placeholder="可用于岗位公开联系方式" onChange={event => setForm(prev => ({ ...prev, applicantWechat: event.target.value }))} />
              </FormCell>
              <FormCell label="补充说明">
                <textarea value={form.note} placeholder="可填写企业官网、部门、授权关系等信息" rows={3} onChange={event => setForm(prev => ({ ...prev, note: event.target.value }))} />
              </FormCell>
            </>
          )}
        </div>

        <div className="cell-group-title">隐私设置</div>
        <div className="cell-group">
          <FormCell label="企业虚拟名">
            <input value={form.virtual} placeholder="选填，前台可用虚拟名展示" onChange={event => setForm(prev => ({ ...prev, virtual: event.target.value }))} />
          </FormCell>
        </div>
      </div>
      <div className="page-foot">
        <button className={`btn ${loading ? 'btn-disabled' : 'btn-primary'}`} onClick={handleSubmit} disabled={loading}>
          {loading ? '提交中...' : certification?.status === 'approved' ? '重新提交认证' : '提交企业认证'}
        </button>
      </div>
    </>
  )
}
