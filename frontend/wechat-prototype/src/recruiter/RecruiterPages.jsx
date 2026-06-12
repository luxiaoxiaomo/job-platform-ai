import React, { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  AIBadge,
  AICard,
  Cell,
  CellGroup,
  EmotionTag,
  FormCell,
  NavBar,
  StatusBadge,
  TabBar,
  useToast,
} from '../components/ui.jsx'
import { followUpReminders, myJobs, pickColor, recruiterChats, talentPool } from '../mock/data.js'
import {
  getCurrentUser,
  getMyCompanyCertification,
  listMyJobs,
  logout,
  submitCompanyCertification,
  uploadBusinessLicenseForOcr,
  uploadCertificationProofFile,
} from '../services/index.js'

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
  const initialTab = searchParams.get('tab') || 'jobs'
  const [tab, setTab] = useState(initialTab)
  const navigate = useNavigate()
  const totalUnread = recruiterChats.reduce((sum, item) => sum + item.unread, 0)

  useEffect(() => {
    const urlTab = searchParams.get('tab')
    if (urlTab && urlTab !== tab) setTab(urlTab)
  }, [searchParams, tab])

  const tabs = [
    { key: 'jobs', label: '岗位', icon: '📋' },
    { key: 'talent', label: '人才', icon: '👥' },
    { key: 'messages', label: '消息', icon: '💬', badge: totalUnread || null },
    { key: 'profile', label: '我的', icon: '👤' },
  ]

  return (
    <>
      {tab === 'jobs' && <JobList onCreate={() => navigate('/recruiter/job/create')} />}
      {tab === 'talent' && <TalentEntry />}
      {tab === 'messages' && <MsgList onOpen={(id) => navigate('/recruiter/chat/' + id)} />}
      {tab === 'profile' && <Profile />}
      <TabBar tabs={tabs} active={tab} onChange={setTab} />
    </>
  )
}

function JobList({ onCreate }) {
  const navigate = useNavigate()
  const toast = useToast()
  const [certification, setCertification] = useState(null)
  const [jobs, setJobs] = useState(myJobs)
  const [jobsLoading, setJobsLoading] = useState(true)
  const [sortBy, setSortBy] = useState('time')
  const [jobStates, setJobStates] = useState({})
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    getMyCompanyCertification()
      .then(setCertification)
      .catch(() => setCertification({ status: 'not_submitted' }))
  }, [])

  useEffect(() => {
    setJobsLoading(true)
    listMyJobs({ limit: 100 })
      .then(data => {
        const mapped = (data.items || []).map(mapApiJobToCard)
        setJobs(mapped.length ? mapped : myJobs)
      })
      .catch(() => setJobs(myJobs))
      .finally(() => setJobsLoading(false))
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
          <span>待跟进候选人（{followUpReminders.length}）</span>
        </div>
        <div className="cell-group">
          {followUpReminders.map(item => (
            <div key={item.id} className="cell link" onClick={() => navigate('/recruiter/talent/' + item.id)}>
              <span className="avatar" style={{ width: 34, height: 34, borderRadius: 6, background: pickColor(item.logoIdx), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 600, marginRight: 10, flexShrink: 0 }}>{item.name[0]}</span>
              <div className="grow" style={{ overflow: 'hidden' }}>
                <div className="row gap6">
                  <span style={{ fontWeight: 500, fontSize: 14 }}>{item.name}</span>
                  {item.level === 'urgent' && <span className="tag tag-red" style={{ fontSize: 10 }}>紧急</span>}
                  <span className="tag tag-green" style={{ fontSize: 10 }}>{item.matchScore}%</span>
                </div>
                <div className="tiny muted" style={{ marginTop: 2 }}>{item.reason}</div>
              </div>
              <span className="cell-arrow">›</span>
            </div>
          ))}
        </div>

        {sorted.map(job => (
          <div key={job.id} className="job-card">
            <div className="jc-top" onClick={() => job.status === 'pending' ? navigate('/recruiter/job/review') : job.status === 'online' ? navigate('/recruiter/job/visitors/' + job.id) : navigate('/recruiter/stats')}>
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
    views: 0,
    uv: 0,
    msgs: 0,
    date: job.created_at ? new Date(job.created_at).toLocaleDateString('zh-CN') : '',
    insight: job.status === 'pending'
      ? '已提交审核，审核通过后会对求职者可见。'
      : '岗位已通过审核，可继续观察浏览与留言数据。',
  }
}

function MsgList({ onOpen }) {
  return (
    <>
      <NavBar title="消息" back={false} />
      <div className="page has-tabbar" style={{ background: '#fff' }}>
        {recruiterChats.map(chat => (
          <div key={chat.id} className="cell link" onClick={() => onOpen(chat.id)} style={{ alignItems: 'flex-start', padding: '12px 16px' }}>
            <span className="msg-avatar avatar" style={{ width: 46, height: 46, borderRadius: 6, background: pickColor(chat.logoIdx), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 17, fontWeight: 600, marginRight: 12, flexShrink: 0 }}>
              {chat.name[0]}
            </span>
            <div className="grow" style={{ overflow: 'hidden' }}>
              <div className="row between">
                <span style={{ fontWeight: 500 }}>{chat.name}{chat.virtual && <span className="tag tag-gray" style={{ marginLeft: 6 }}>虚拟名</span>}</span>
                <span className="tiny muted">{chat.time}</span>
              </div>
              <div className="row" style={{ marginTop: 3, gap: 6 }}>
                <EmotionTag level={chat.emotion} />
                <span className="tiny muted" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{chat.preview}</span>
              </div>
              <div className="tiny" style={{ color: 'var(--wx-text-light)', marginTop: 3 }}>应聘：{chat.job}</div>
            </div>
            {chat.unread > 0 && <span className="tab-badge" style={{ position: 'static', marginLeft: 8 }}>{chat.unread}</span>}
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
  const certMeta = getCertMeta(certification?.status)

  useEffect(() => {
    getMyCompanyCertification()
      .then(setCertification)
      .catch(() => setCertification({ status: 'not_submitted' }))
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
          <Cell icon="📋" iconBg="#ECF9F1" label="我的岗位" value="3 在线 · 2 审核中" link onClick={() => navigate('/recruiter/jobs')} />
          <Cell icon="👥" iconBg="#E8F5FF" label="人才池" value="21 人" link onClick={() => navigate('/recruiter/talent')} />
          <Cell icon="📅" iconBg="#FFF3E6" label="面试管理" value="2 待面试" link onClick={() => navigate('/recruiter/interviews')} />
          <Cell icon="📊" iconBg="#FFF3E6" label="候选人分析" value="8 人" link onClick={() => navigate('/recruiter/candidate')} />
          <Cell icon="🏢" iconBg="#E8F5FF" label="企业画像" value="AI 生成" link onClick={() => navigate('/recruiter/company-portrait')} />
          <Cell icon="📈" iconBg="#E8F5FF" label="数据统计" link onClick={() => navigate('/recruiter/stats')} />
          <Cell icon="✓" iconBg="#FFF3E6" label="企业认证" value={certMeta.text} link onClick={() => navigate('/recruiter/register')} />
        </CellGroup>
        <CellGroup>
          <Cell icon="🔔" iconBg="#FFE6E6" label="通知中心" value="2 条未读" link onClick={() => navigate('/recruiter/notifications')} />
          <Cell icon="💬" iconBg="#ECF9F1" label="智能客服" link onClick={() => navigate('/support')} />
          <Cell icon="🛡" iconBg="#E8F5FF" label="隐私与公开设置" link />
          <Cell icon="⚙" iconBg="#F2F2F2" label="账号设置" link />
        </CellGroup>
        <div className="btn-block-wrap"><button className="btn btn-default" onClick={logout}>退出登录</button></div>
      </div>
    </>
  )
}

function TalentEntry() {
  const navigate = useNavigate()
  const activeTalents = talentPool.filter(item => item.status === 'active').slice(0, 5)

  return (
    <>
      <NavBar title="人才池" back={false} right={<span style={{ color: 'var(--wx-green)' }} onClick={() => navigate('/recruiter/talent')}>查看全部 ›</span>} />
      <div className="page has-tabbar">
        <div className="row" style={{ background: '#fff', padding: '16px', gap: 0 }}>
          {[
            ['总人才', 21],
            ['本月新增', 8],
            ['活跃沟通', 5],
            ['高匹配', 4],
          ].map(([label, value]) => (
            <div key={label} className="grow center">
              <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{label}</div>
            </div>
          ))}
        </div>

        <div className="cell-group-title">活跃人才（最近互动）</div>
        <div className="cell-group">
          {activeTalents.map(item => (
            <div key={item.id} className="cell link" onClick={() => navigate('/recruiter/talent/' + item.id)}>
              <span className="avatar" style={{ width: 36, height: 36, borderRadius: 6, background: pickColor(item.logoIdx), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 600, marginRight: 10, flexShrink: 0 }}>{item.name[0]}</span>
              <span className="grow" style={{ fontSize: 14 }}>{item.name}{item.virtual && <span className="tag tag-gray" style={{ marginLeft: 4, fontSize: 10 }}>虚拟</span>}</span>
              <span className="tag tag-green" style={{ fontSize: 12 }}>{item.matchAvg}%</span>
              <span className="cell-arrow">›</span>
            </div>
          ))}
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
