import React, { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { NavBar, HomeNavLink, AIBadge, AICard, Sheet, useToast } from '../components/ui.jsx'
import { RadarChart } from '../components/charts.jsx'
import {
  addMyJobFavorite,
  createApplication,
  getMyApplication,
  getMyJobMatch,
  getMyResume,
  getPublicCompanyCertification,
  getStructuredResult,
  listMyApplications,
  listMyJobFavorites,
  listMyJobHistory,
  removeMyJobFavorite,
  suggestApplicationCoverLetter,
  uploadResume,
} from '../services/index.js'
import { findPublicJobById } from '../utils/jobView.js'
import { applicationStatusTag, applicationStatusText, formatDateTime } from '../utils/applicationView.js'

function formatJobSalary(job) {
  if (!job) return ''
  if (job.salary_min && job.salary_max) return `${job.salary_min}K-${job.salary_max}K`
  if (job.salary_min) return `${job.salary_min}K+`
  if (job.salary) return job.salary
  return ''
}

function formatShortDateTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function normalizeStructuredBasic(basic) {
  if (!basic) return null
  const extractValue = (field) => {
    if (!field) return null
    if (typeof field === 'object' && 'value' in field) return field.value
    return field
  }
  return {
    real_name: extractValue(basic.real_name) || extractValue(basic.name) || null,
    gender: extractValue(basic.gender) || null,
    age: extractValue(basic.age) ?? null,
    highest_education: extractValue(basic.highest_education) || extractValue(basic.education) || null,
    work_years: extractValue(basic.work_years) ?? extractValue(basic.experience_years) ?? null,
    target_position: extractValue(basic.target_position) || extractValue(basic.apply_job) || null,
  }
}

export function SeekerMatch() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    getMyJobMatch(id)
      .then(result => {
        setData(result)
        setError('')
      })
      .catch(err => {
        setData(null)
        setError(err.message || '匹配分析加载失败')
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <>
        <NavBar title="AI 人岗匹配分析" right={<HomeNavLink />} />
        <div className="page" style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>加载中...</div>
      </>
    )
  }

  if (error || !data) {
    return (
      <>
        <NavBar title="AI 人岗匹配分析" right={<HomeNavLink />} />
        <div className="page" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ color: '#999', marginBottom: 20 }}>{error || '暂时无法生成匹配分析'}</div>
          <button className="btn btn-primary" onClick={() => navigate(-1)}>返回</button>
        </div>
      </>
    )
  }

  const dimensions = data.dimensions || []
  const levelColor = data.level === 'high' ? '#07C160' : data.level === 'medium' ? '#FA9D3B' : '#FA5151'
  const levelText = data.level === 'high' ? '高度匹配' : data.level === 'medium' ? '中度匹配' : '匹配度较低'
  const radarData = dimensions.map(d => ({ key: d.label || d.key, score: d.score || 0 }))

  return (
    <>
      <NavBar title="AI 人岗匹配分析" right={<HomeNavLink />} />
      <div className="page">
        <div className="center" style={{ background: '#fff', padding: '20px 0 6px' }}>
          <div className="tiny muted">你与“{data.job?.title || '当前岗位'}”的匹配度</div>
          <div style={{ fontSize: 44, fontWeight: 800, color: levelColor, lineHeight: 1.2 }}>
            {data.overall_score}<span style={{ fontSize: 18 }}>分</span>
          </div>
          <span className="tag" style={{ background: '#F7F8FA', color: levelColor, border: 'none' }}>{levelText}</span>
          <div className="tiny" style={{ marginTop: 8, color: '#666' }}>{data.recommendation}</div>
        </div>

        {dimensions.length > 0 && dimensions.length <= 8 && (
          <div className="center" style={{ background: '#fff', paddingBottom: 10 }}>
            <RadarChart data={radarData} size={240} />
          </div>
        )}

        <div className="cell-group-title">分项得分</div>
        <div className="cell-group">
          <div style={{ padding: '14px 16px 4px' }}>
            {dimensions.length === 0 && <div className="tiny muted">暂无分项得分</div>}
            {dimensions.map(d => {
              const effectiveWeight = d.effective_weight || d.weight || 0
              const weightedScore = d.weighted_score !== undefined
                ? Math.round(d.weighted_score)
                : Math.round((d.score || 0) * effectiveWeight / 100)
              return (
                <div key={d.key || d.label} style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 13, color: '#333', marginBottom: 6, fontWeight: 500 }}>{d.label || d.key}</div>
                  <div className="row between tiny" style={{ marginBottom: 4 }}>
                    <span style={{ color: '#999' }}>得分 {d.score}分</span>
                    <span style={{ color: '#999' }}>权重 {effectiveWeight}% / 贡献 {weightedScore}分</span>
                  </div>
                  <div className="progress">
                    <div className="bar" style={{ width: `${d.score || 0}%`, background: (d.score || 0) >= 85 ? '#07C160' : (d.score || 0) >= 70 ? '#FA9D3B' : '#FA5151' }} />
                  </div>
                  {d.scoring_method && <div className="tiny muted" style={{ marginTop: 4, lineHeight: 1.5 }}>{d.scoring_method}</div>}
                </div>
              )
            })}
          </div>
        </div>

        {(data.highlights || []).length > 0 && (
          <>
            <div className="cell-group-title">匹配亮点</div>
            <div className="cell-group"><div style={{ padding: 16 }}>{data.highlights.map((h, i) => <div key={i} className="tiny" style={{ marginBottom: 8, lineHeight: 1.6 }}>{h}</div>)}</div></div>
          </>
        )}
        {(data.gaps || []).length > 0 && (
          <>
            <div className="cell-group-title">待补充项</div>
            <div className="cell-group"><div style={{ padding: 16 }}>{data.gaps.map((g, i) => <div key={i} className="tiny" style={{ marginBottom: 8, lineHeight: 1.6 }}>{g}</div>)}</div></div>
          </>
        )}

        <div className="btn-block-wrap">
          <button className="btn btn-default" onClick={() => navigate('/seeker/job/' + id)}>返回岗位详情</button>
          <button className="btn btn-primary" onClick={() => navigate('/seeker/home')}>回首页</button>
        </div>
      </div>
    </>
  )
}

export function SeekerApply() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const fileInputRef = useRef(null)
  const [job, setJob] = useState(null)
  const [resume, setResume] = useState(null)
  const [resumeBasic, setResumeBasic] = useState(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [coverMessage, setCoverMessage] = useState('')
  const [generatingCover, setGeneratingCover] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')

  const loadStructuredResult = async (parseRunId) => {
    if (!parseRunId) {
      setResumeBasic(null)
      return
    }
    try {
      const structured = await getStructuredResult(parseRunId)
      if (structured.basic_info) setResumeBasic(structured.basic_info)
      else if (structured.basic) setResumeBasic(normalizeStructuredBasic(structured.basic))
      else if (structured.profile?.structured_json?.basic) setResumeBasic(normalizeStructuredBasic(structured.profile.structured_json.basic))
      else setResumeBasic(null)
    } catch {
      setResumeBasic(null)
    }
  }

  useEffect(() => {
    let alive = true
    setLoading(true)
    Promise.allSettled([findPublicJobById(id), getMyResume()])
      .then(async ([jobResult, resumeResult]) => {
        if (!alive) return
        if (jobResult.status === 'fulfilled') setJob(jobResult.value)
        if (resumeResult.status === 'fulfilled') {
          const currentResume = resumeResult.value.resume || null
          setResume(currentResume)
          await loadStructuredResult(currentResume?.current_parse_run_id || resumeResult.value.latest_parse_run?.id)
        }
      })
      .catch(err => {
        if (alive) setError(err.message || '页面加载失败')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => { alive = false }
  }, [id])

  const onResumeFileChange = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file || uploading) return
    setUploading(true)
    setError('')
    try {
      const uploaded = await uploadResume(file)
      setResume(uploaded.resume || uploaded)
      const parseRunId = uploaded.parse_run?.id || uploaded.current_parse_run_id
      await loadStructuredResult(parseRunId)
      toast('简历已上传并解析', '✓')
    } catch (err) {
      setError(err.message || '简历上传失败')
      toast(err.message || '简历上传失败')
    } finally {
      setUploading(false)
    }
  }

  const submitApplication = async () => {
    if (submitting || submitted) return
    if (!resume) {
      toast('请先上传简历')
      fileInputRef.current?.click()
      return
    }
    setSubmitting(true)
    setError('')
    try {
      await createApplication({
        job_id: Number(id),
        cover_message: coverMessage.trim() || `申请岗位：${job?.name || job?.title || id}`,
      })
      setSubmitted(true)
      toast('投递成功', '✓')
    } catch (err) {
      setError(err.message || '投递失败')
      toast(err.message || '投递失败')
    } finally {
      setSubmitting(false)
    }
  }

  const generateCoverMessage = async () => {
    if (generatingCover) return
    setGeneratingCover(true)
    setError('')
    try {
      const result = await suggestApplicationCoverLetter({ job_id: Number(id) })
      setCoverMessage(result.cover_message || '')
      toast('AI 求职信已生成', '✓')
    } catch (err) {
      const fallback = `您好，我希望投递「${job?.name || job?.title || id}」。我已上传简历，对该岗位比较感兴趣，期待有机会进一步沟通，谢谢。`
      setCoverMessage(fallback)
      toast(err.message || 'AI 生成失败，已使用模板')
    } finally {
      setGeneratingCover(false)
    }
  }

  return (
    <>
      <NavBar title="确认投递" onBack={() => navigate('/seeker/job/' + id)} right={<HomeNavLink />} />
      <div className="page" style={{ paddingBottom: 90 }}>
        {loading && <div className="empty" style={{ padding: '40px 20px' }}><div className="tiny muted">正在加载...</div></div>}
        {job && (
          <div className="job-card">
            <div className="jc-top"><span className="jc-name">{job.name || job.title}</span><span className="jc-salary">{job.salary || formatJobSalary(job.raw)}</span></div>
            <div className="jc-company"><span className="jc-logo">{(job.companyShow || '企')[0]}</span><span>{job.companyShow || '认证企业'}</span></div>
          </div>
        )}

        {submitted && (
          <div className="ai-card center">
            <div className="ai-card-hd">投递成功</div>
            <div className="ai-card-bd">你可以继续浏览岗位，或查看投递记录跟进进度。</div>
            <div className="row gap8" style={{ justifyContent: 'center', marginTop: 12 }}>
              <button className="btn btn-default btn-sm" onClick={() => navigate('/seeker/home')}>回首页</button>
              <button className="btn btn-primary btn-sm" onClick={() => navigate('/seeker/applications')}>查看投递记录</button>
            </div>
          </div>
        )}

        <div className="cell-group-title">将投递以下简历</div>
        <div className="cell-group">
          <input ref={fileInputRef} type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.webp,.bmp" style={{ display: 'none' }} onChange={onResumeFileChange} />
          {resume ? (
            <>
              <div className="cell"><span className="cell-label">简历文件</span><span className="cell-value">{resume.file_name}</span></div>
              <div className="cell"><span className="cell-label">姓名</span><span className="cell-value">{resumeBasic?.real_name || '未识别'}</span></div>
              <div className="cell"><span className="cell-label">年龄</span><span className="cell-value">{resumeBasic?.age ? `${resumeBasic.age}岁` : '未识别'}</span></div>
              <div className="cell"><span className="cell-label">性别</span><span className="cell-value">{resumeBasic?.gender || '未识别'}</span></div>
              <div className="cell"><span className="cell-label">学历</span><span className="cell-value">{resumeBasic?.highest_education || '未识别'}</span></div>
              <div className="cell link" onClick={() => fileInputRef.current?.click()}><span className="cell-label">重新上传</span><span className="cell-value">{uploading ? '上传中...' : '更换简历'}</span></div>
            </>
          ) : (
            <div className="cell link" onClick={() => fileInputRef.current?.click()}><span className="cell-label">简历</span><span className="cell-value" style={{ color: 'var(--wx-red)' }}>{uploading ? '上传中...' : '点击上传'}</span></div>
          )}
        </div>

        <AICard title="AI 匹配提示">投递前可查看岗位匹配分析，确认简历画像是否完整。</AICard>
        <div className="cell-group-title">AI 求职信</div>
        <div className="cell-group" style={{ padding: 16 }}>
          <div className="row between" style={{ marginBottom: 10 }}>
            <span className="tiny muted">可编辑后随投递一起发送给招聘者</span>
            <button type="button" className={`btn btn-sm ${generatingCover ? 'btn-disabled' : 'btn-default'}`} onClick={generateCoverMessage}>
              {generatingCover ? '生成中...' : 'AI 生成'}
            </button>
          </div>
          <textarea
            value={coverMessage}
            onChange={event => setCoverMessage(event.target.value)}
            maxLength={1000}
            placeholder="可以写几句你对岗位的兴趣、匹配技能和可沟通时间"
            style={{
              width: '100%',
              minHeight: 110,
              border: '1px solid var(--wx-line-light)',
              borderRadius: 8,
              padding: 10,
              resize: 'vertical',
              boxSizing: 'border-box',
              fontSize: 14,
              lineHeight: 1.6,
              outline: 'none',
            }}
          />
          <div className="tiny muted" style={{ textAlign: 'right', marginTop: 6 }}>{coverMessage.length}/1000</div>
        </div>
        {error && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>}
      </div>
      <div className="page-foot">
        <button className="btn btn-default" style={{ flex: '0 0 96px' }} onClick={() => navigate('/seeker/job/' + id)}>返回岗位</button>
        <button className={`btn ${submitting || uploading || submitted ? 'btn-disabled' : 'btn-primary'}`} onClick={submitApplication}>
          {submitted ? '已投递' : submitting ? '提交中...' : resume ? '确认投递' : '上传简历'}
        </button>
      </div>
    </>
  )
}

export function SeekerApplications() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const detailId = searchParams.get('applicationId')
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (detailId) return undefined
    let alive = true
    setLoading(true)
    listMyApplications({ limit: 100 })
      .then(data => {
        if (!alive) return
        setApplications(data.items || [])
        setError('')
      })
      .catch(err => {
        if (!alive) return
        setApplications([])
        setError(err.message || '投递记录加载失败')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => { alive = false }
  }, [detailId])

  if (detailId) return <SeekerApplicationDetail applicationIdOverride={detailId} />

  return (
    <>
      <NavBar title="投递记录" right={<HomeNavLink />} />
      <div className="page">
        {loading && <div className="empty" style={{ padding: '40px 20px' }}><div className="tiny muted">正在加载投递记录...</div></div>}
        {error && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>}
        {!loading && !error && applications.length === 0 && <div className="empty" style={{ padding: '60px 20px' }}><div className="tiny muted">暂无真实投递记录</div></div>}
        {!loading && !error && applications.map(a => (
          <div key={a.id} className="job-card" onClick={() => navigate(`/seeker/applications?applicationId=${a.id}`)}>
            <div className="jc-top"><span className="jc-name">{a.job_title || `岗位 #${a.job_id}`}</span><span className={`tag ${applicationStatusTag[a.status] || 'tag-gray'}`}>{applicationStatusText[a.status] || a.status}</span></div>
            <div className="jc-meta"><span className="tag tag-gray">{a.job_city || '-'}</span><span className="tag tag-gray">{formatDateTime(a.created_at)}</span></div>
            <div className="tiny muted" style={{ marginTop: 6 }}>{a.resume_file_name || '未记录简历文件名'}</div>
          </div>
        ))}
      </div>
    </>
  )
}

export function SeekerApplicationDetail({ applicationIdOverride } = {}) {
  const { applicationId } = useParams()
  const resolvedApplicationId = applicationIdOverride || applicationId
  const navigate = useNavigate()
  const [application, setApplication] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    setLoading(true)
    getMyApplication(resolvedApplicationId)
      .then(data => {
        if (!alive) return
        setApplication(data)
        setError('')
      })
      .catch(err => {
        if (!alive) return
        setApplication(null)
        setError(err.message || '投递详情加载失败')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => { alive = false }
  }, [resolvedApplicationId])

  const timeline = application?.timeline || []

  return (
    <>
      <NavBar title="投递详情" right={<HomeNavLink />} />
      <div className="page">
        {loading && <div className="empty" style={{ padding: '60px 20px' }}><div className="tiny muted">正在加载投递详情...</div></div>}
        {error && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>}
        {application && (
          <>
            <div className="job-card">
              <div className="jc-top"><span className="jc-name">{application.job_title || `岗位 #${application.job_id}`}</span><span className={`tag ${applicationStatusTag[application.status] || 'tag-gray'}`}>{applicationStatusText[application.status] || application.status}</span></div>
              <div className="tiny muted" style={{ marginTop: 6 }}>投递时间：{formatDateTime(application.created_at)}</div>
            </div>
            <div className="cell-group-title">投递简历</div>
            <div className="cell-group"><div className="cell"><span className="cell-label">{application.resume_file_name || '未记录简历文件名'}</span></div></div>
            <div className="cell-group-title">状态时间线</div>
            <div className="cell-group">
              {timeline.length === 0 && <div className="cell"><span className="grow tiny muted">暂无状态记录</span></div>}
              {timeline.map(item => (
                <div key={item.id} className="cell" style={{ alignItems: 'flex-start' }}>
                  <span style={{ width: 8, height: 8, borderRadius: 999, background: 'var(--wx-green)', margin: '7px 12px 0 2px', flexShrink: 0 }} />
                  <div className="grow">
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{applicationStatusText[item.to_status] || item.to_status}</div>
                    <div className="tiny muted" style={{ marginTop: 3 }}>{formatDateTime(item.created_at)}</div>
                    {item.note && <div className="tiny" style={{ marginTop: 3, color: 'var(--wx-text-2)' }}>{item.note}</div>}
                  </div>
                </div>
              ))}
            </div>
            <div className="btn-block-wrap row gap8">
              <button className="btn btn-default" onClick={() => navigate('/seeker/applications')}>返回记录</button>
              <button className="btn btn-default" onClick={() => navigate('/seeker/home')}>回首页</button>
              <button className="btn btn-primary" onClick={() => navigate('/seeker/job/' + application.job_id)}>查看岗位</button>
            </div>
          </>
        )}
      </div>
    </>
  )
}

export function SeekerFavorites() {
  const navigate = useNavigate()
  const toast = useToast()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    listMyJobFavorites({ limit: 100 })
      .then(data => {
        setItems(data.items || [])
        setError('')
      })
      .catch(err => {
        setItems([])
        setError(err.message || '收藏加载失败')
      })
      .finally(() => setLoading(false))
  }, [])

  const removeFavorite = async (event, jobId) => {
    event.stopPropagation()
    try {
      await removeMyJobFavorite(jobId)
      setItems(arr => arr.filter(item => item.job?.id !== jobId))
      toast('已取消收藏')
    } catch (err) {
      toast(err.message || '取消收藏失败')
    }
  }

  return (
    <>
      <NavBar title="我的收藏" right={<HomeNavLink />} />
      <div className="page">
        {loading && <div className="empty" style={{ padding: '60px 20px' }}><div className="tiny muted">正在加载收藏...</div></div>}
        {error && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>}
        {!loading && !error && items.length === 0 && <div className="empty" style={{ paddingTop: 100, textAlign: 'center' }}><div className="tiny muted">暂无收藏职位</div></div>}
        {!loading && !error && items.map(item => {
          const j = item.job
          return (
            <div key={item.id} className="job-card" onClick={() => navigate('/seeker/job/' + j.id)}>
              <div className="jc-top"><span className="jc-name" style={{ fontSize: 15 }}>{j.title}</span><span className="jc-salary" style={{ fontSize: 15 }}>{formatJobSalary(j)}</span></div>
              <div className="jc-meta"><span className="tag tag-gray">{j.city}</span><span className="tag tag-gray">{j.experience}</span><span className="tag tag-gray">{j.education}</span></div>
              <div className="jc-company"><span className="jc-logo">{(j.recruiter_display_name || '企')[0]}</span><span>{j.recruiter_display_name || '认证企业'}</span><span className="grow" /><span className="tiny muted">{formatShortDateTime(item.created_at)}</span><span className="tiny" style={{ color: 'var(--wx-red)', marginLeft: 8 }} onClick={(e) => removeFavorite(e, j.id)}>取消收藏</span></div>
            </div>
          )
        })}
      </div>
    </>
  )
}

export function SeekerHistory() {
  const navigate = useNavigate()
  const toast = useToast()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    listMyJobHistory({ limit: 100 })
      .then(data => {
        setItems(data.items || [])
        setError('')
      })
      .catch(err => {
        setItems([])
        setError(err.message || '浏览记录加载失败')
      })
      .finally(() => setLoading(false))
  }, [])

  const addFavorite = async (event, jobId) => {
    event.stopPropagation()
    try {
      await addMyJobFavorite(jobId)
      setItems(arr => arr.map(item => item.job?.id === jobId ? { ...item, is_favorited: true } : item))
      toast('已收藏')
    } catch (err) {
      toast(err.message || '收藏失败')
    }
  }

  return (
    <>
      <NavBar title="浏览记录" right={<HomeNavLink />} />
      <div className="page">
        {loading && <div className="empty" style={{ padding: '60px 20px' }}><div className="tiny muted">正在加载浏览记录...</div></div>}
        {error && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>}
        {!loading && !error && items.length === 0 && <div className="empty" style={{ paddingTop: 100, textAlign: 'center' }}><div className="tiny muted">暂无浏览记录</div></div>}
        {!loading && !error && items.map(item => {
          const j = item.job
          return (
            <div key={j.id} className="job-card" onClick={() => navigate('/seeker/job/' + j.id)}>
              <div className="jc-top"><span className="jc-name" style={{ fontSize: 15 }}>{j.title}</span><span className="jc-salary" style={{ fontSize: 15 }}>{formatJobSalary(j)}</span></div>
              <div className="jc-meta"><span className="tag tag-gray">{j.city}</span><span className="tag tag-gray">{j.experience}</span><span className="tag tag-green">浏览 {item.view_count} 次</span></div>
              <div className="jc-company"><span className="jc-logo">{(j.recruiter_display_name || '企')[0]}</span><span>{j.recruiter_display_name || '认证企业'}</span><span className="grow" /><span className="tiny muted">{formatShortDateTime(item.last_viewed_at)}</span>{!item.is_favorited ? <span className="tiny" style={{ color: 'var(--wx-green)', marginLeft: 8 }} onClick={(e) => addFavorite(e, j.id)}>收藏</span> : <span className="tiny muted" style={{ marginLeft: 8 }}>已收藏</span>}</div>
            </div>
          )
        })}
      </div>
    </>
  )
}

export function SeekerInterviewPrep() {
  const navigate = useNavigate()
  return (
    <>
      <NavBar title="AI 面试准备" right={<HomeNavLink />} />
      <div className="page">
        <AICard title="面试准备">面试准备能力后续将基于岗位 JD 和你的简历画像生成。</AICard>
      </div>
    </>
  )
}

export function SeekerCompanyView() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const recruiterId = searchParams.get('recruiterId')
  const [company, setCompany] = useState(null)
  const [loading, setLoading] = useState(!!recruiterId)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!recruiterId) {
      setLoading(false)
      setError('未关联招聘者，无法查看真实企业画像。')
      return
    }
    getPublicCompanyCertification(recruiterId)
      .then(data => {
        setCompany(data)
        setError('')
      })
      .catch(err => {
        setCompany(null)
        setError(err.message || '企业画像加载失败')
      })
      .finally(() => setLoading(false))
  }, [recruiterId])

  return (
    <>
      <NavBar title="企业画像" right={<HomeNavLink />} />
      <div className="page">
        {loading && <div className="empty" style={{ padding: '30px 20px' }}><div className="tiny muted">正在加载企业画像...</div></div>}
        {error && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>}
        {company && (
          <>
            <div className="portrait-hd"><div className="ph-name">{company.company_name}</div><span className="ph-level">平台企业认证通过</span></div>
            <div className="cell-group">
              <div className="cell"><span className="cell-label">统一社会信用代码</span><span className="cell-value">{company.unified_social_credit_code || '-'}</span></div>
              <div className="cell"><span className="cell-label">法定代表人</span><span className="cell-value">{company.legal_representative || '-'}</span></div>
              <div className="cell"><span className="cell-label">注册地址</span><span className="cell-value">{company.registered_address || '-'}</span></div>
            </div>
          </>
        )}
      </div>
    </>
  )
}

export function ShareSheet({ title, onClose }) {
  const toast = useToast()
  const channels = ['微信好友', '朋友圈', '复制链接']
  return (
    <Sheet title={title || '分享到'} onClose={onClose}>
      <div className="row" style={{ justifyContent: 'space-around', padding: '6px 0 16px' }}>
        {channels.map(label => (
          <div key={label} className="center" onClick={() => { toast(label === '复制链接' ? '已复制' : `已分享至${label}`); onClose?.() }}>
            <div style={{ width: 50, height: 50, borderRadius: '50%', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, margin: '0 auto 6px' }}>{label.slice(0, 1)}</div>
            <div className="tiny muted">{label}</div>
          </div>
        ))}
      </div>
    </Sheet>
  )
}
