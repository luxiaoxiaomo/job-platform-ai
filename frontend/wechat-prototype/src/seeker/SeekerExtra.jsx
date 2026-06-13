import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, AIBadge, AICard, useToast, Sheet } from '../components/ui.jsx'
import { RadarChart, ScoreBar } from '../components/charts.jsx'
import { matchAnalysis, favoriteJobs, companyProfile, interviewPrep, getFeedJob, pickColor } from '../mock/data.js'
import { createApplication, listMyApplications } from '../services/index.js'
import { findPublicJobById } from '../utils/jobView.js'
import { applicationStatusTag, applicationStatusText, formatDateTime } from '../utils/applicationView.js'

/* ============ 人岗匹配分析（应聘者：我 vs 岗位） ============ */
export function SeekerMatch() {
  const { id } = useParams()
  const navigate = useNavigate()
  const job = getFeedJob(id) || getFeedJob('1')
  const m = matchAnalysis
  return (
    <>
      <NavBar title="AI 人岗匹配分析" />
      <div className="page">
        <div className="center" style={{ background: '#fff', padding: '20px 0 6px' }}>
          <div className="tiny muted">你与「{job.name}」的匹配度</div>
          <div style={{ fontSize: 44, fontWeight: 800, color: 'var(--wx-green)', lineHeight: 1.2 }}>{m.score}<span style={{ fontSize: 18 }}>分</span></div>
          <span className="tag tag-green">高度匹配</span>
        </div>

        <div className="center" style={{ background: '#fff', paddingBottom: 10 }}>
          <RadarChart data={m.dims} size={240} />
        </div>

        <AICard title="AI 匹配结论" tip="AI 分析，仅供参考">{m.summary}</AICard>

        <div className="cell-group-title">分项得分</div>
        <div className="cell-group"><div style={{ padding: '14px 16px 4px' }}>
          {m.dims.map(d => (
            <div key={d.key} style={{ marginBottom: 10 }}>
              <ScoreBar label={`${d.key}　${d.note}`} score={d.score} color={d.score >= 85 ? '#07C160' : d.score >= 70 ? '#FA9D3B' : '#FA5151'} />
            </div>
          ))}
        </div></div>

        <div className="cell-group-title">⚡ AI 提升建议</div>
        <div className="cell-group"><div style={{ padding: 16 }}>
          {m.gaps.map((g, i) => (
            <div key={i} className="row gap8" style={{ marginBottom: 10, alignItems: 'flex-start' }}>
              <span style={{ color: 'var(--wx-green)' }}>•</span><span className="tiny" style={{ lineHeight: 1.6 }}>{g}</span>
            </div>
          ))}
        </div></div>

        <div className="btn-block-wrap">
          <button className="btn btn-primary" onClick={() => navigate('/seeker/job/' + job.id)}>返回岗位详情</button>
        </div>
      </div>
    </>
  )
}

/* ============ 简历投递 ============ */
export function SeekerApply() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const fallbackJob = getFeedJob(id) || getFeedJob('1')
  const [job, setJob] = useState(fallbackJob)
  const [done, setDone] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    findPublicJobById(id)
      .then(realJob => {
        if (!alive) return
        if (realJob) {
          setJob(realJob)
          setError('')
          return
        }
        setJob(fallbackJob)
        setError('未找到真实公开岗位，无法提交真实投递。')
      })
      .catch(err => {
        if (!alive) return
        setJob(fallbackJob)
        setError(err.message || '岗位加载失败。')
      })
    return () => { alive = false }
  }, [id])

  const submitApplication = async () => {
    if (submitting || done) return
    if (!Number(id)) {
      setError('当前岗位不是后端真实岗位，不能提交投递。')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      await createApplication({
        job_id: Number(id),
        resume_snapshot: '李然（虚拟名）｜5年｜前端开发｜本科｜期望薪资 22K-30K',
        cover_message: `申请岗位：${job.name}`,
      })
      setDone(true)
      toast('投递成功', '✓')
      setTimeout(() => navigate('/seeker/applications'), 1000)
    } catch (err) {
      const message = err.message || '投递失败'
      setError(message)
      toast(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <NavBar title="投递简历" />
      <div className="page" style={{ paddingBottom: 90 }}>

        <div className="job-card">
          <div className="jc-top"><span className="jc-name">{job.name}</span><span className="jc-salary">{job.salary}</span></div>
          <div className="jc-company"><span className="jc-logo">{job.companyShow[0]}</span><span>{job.companyShow}</span></div>
        </div>

        <div className="cell-group-title">将投递以下简历</div>
        <div className="cell-group">
          <div className="cell"><span className="cell-label">姓名</span><span className="cell-value">李然（虚拟名）</span></div>
          <div className="cell"><span className="cell-label">经验</span><span className="cell-value">5年 · 前端开发</span></div>
          <div className="cell"><span className="cell-label">学历</span><span className="cell-value">本科</span></div>
          <div className="cell"><span className="cell-label">期望薪资</span><span className="cell-value">22K-30K</span></div>
        </div>

        <AICard title="AI 匹配提示">该岗位与你的匹配度 <b>92%</b>，建议投递。<span style={{ color: 'var(--wx-text-2)' }} onClick={() => navigate('/seeker/match/' + job.id)}>查看匹配分析 ›</span></AICard>

        {error && <div className="ai-tip padx" style={{ marginTop: 12, color: 'var(--wx-red)' }}>{error}</div>}
        {done && <div className="center" style={{ padding: 20, color: 'var(--wx-green)' }}>✓ 投递成功，可在「投递记录」查看进度</div>}
      </div>
      <div className="page-foot">
        <button className={`btn ${submitting || done ? 'btn-disabled' : 'btn-primary'}`} onClick={submitApplication}>
          {submitting ? '提交中...' : done ? '已投递' : '确认投递'}
        </button>
      </div>
    </>
  )
}

/* ============ 投递记录（含状态时间线） ============ */
export function SeekerApplications() {
  const navigate = useNavigate()
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedId, setExpandedId] = useState(null)

  useEffect(() => {
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
  }, [])

  return (
    <>
      <NavBar title="投递记录" />
      <div className="page">
        <div className="ai-tip padx" style={{ paddingTop: 12 }}>⚡ 点击卡片可查看投递进度详情</div>
        {loading && <div className="empty" style={{ padding: '40px 20px' }}><div className="tiny muted">正在加载投递记录...</div></div>}
        {error && <div className="ai-tip padx" style={{ marginTop: 12, color: 'var(--wx-red)' }}>{error}</div>}
        {!loading && !error && applications.length === 0 && (
          <div className="empty" style={{ padding: '60px 20px' }}><div className="tiny muted">暂无真实投递记录</div></div>
        )}
        {!loading && !error && applications.map(a => {
          const isExpanded = expandedId === a.id
          const statusText = applicationStatusText[a.status] || a.status
          return (
            <div key={a.id} className="job-card" onClick={() => setExpandedId(isExpanded ? null : a.id)}>
              <div className="jc-top">
                <span className="jc-name" style={{ fontSize: 15 }}>{a.job_title || `岗位 #${a.job_id}`}</span>
                <span className={`tag ${applicationStatusTag[a.status] || 'tag-gray'}`}>{statusText}</span>
              </div>
              <div className="jc-meta">
                <span className="tag tag-gray">{a.recruiter_display_name || '认证企业'}</span>
                {a.job_city && <span className="tag tag-gray">{a.job_city}</span>}
              </div>
              <div className="row between tiny muted" style={{ marginTop: 6 }}>
                <span>投递时间：{formatDateTime(a.created_at)}</span>
                <span style={{ color: 'var(--wx-green-dark)' }}>{isExpanded ? '收起 ▲' : '查看进度 ▼'}</span>
              </div>

              {/* 状态时间线 */}
              {isExpanded && (
                <div style={{ marginTop: 10, paddingTop: 10, borderTop: '0.5px solid var(--wx-line-light)' }} onClick={e => e.stopPropagation()}>
                  <div className="row" style={{ alignItems: 'flex-start', gap: 10, marginBottom: 8 }}>
                    <span style={{ fontSize: 14, color: 'var(--wx-green)', flexShrink: 0 }}>●</span>
                    <div className="grow">
                      <div style={{ fontSize: 13, fontWeight: 500 }}>已提交给招聘者</div>
                      <div className="tiny muted">{formatDateTime(a.created_at)}</div>
                    </div>
                  </div>
                  {a.status !== 'submitted' && (
                    <div className="row" style={{ alignItems: 'flex-start', gap: 10, marginBottom: 8 }}>
                      <span style={{ fontSize: 14, color: 'var(--wx-green)', flexShrink: 0 }}>●</span>
                      <div className="grow">
                        <div style={{ fontSize: 13, fontWeight: 500 }}>{statusText}</div>
                        {a.status_updated_at && <div className="tiny muted">{formatDateTime(a.status_updated_at)}</div>}
                        {a.reject_reason && <div className="tiny muted" style={{ marginTop: 2 }}>{a.reject_reason}</div>}
                      </div>
                    </div>
                  )}
                  {a.status === 'interview_invited' && (
                    <button className="btn btn-primary btn-sm" style={{ marginTop: 4 }} onClick={() => navigate('/seeker/interview-prep')}>📋 AI 面试准备</button>
                  )}
                </div>
              )}
            </div>
          )
        })}
        {!loading && !error && applications.length > 0 && <div className="empty" style={{ padding: '30px 20px' }}><div className="tiny">仅展示最近投递</div></div>}
      </div>
    </>
  )
}

/* ============ 收藏夹 ============ */
export function SeekerFavorites() {
  const navigate = useNavigate()
  const toast = useToast()
  return (
    <>
      <NavBar title="我的收藏" />
      <div className="page">
        {favoriteJobs.map(j => (
          <div key={j.id} className="job-card" onClick={() => !j.offline && navigate('/seeker/job/' + j.id)}>
            <div className="jc-top">
              <span className="jc-name" style={{ fontSize: 15 }}>{j.name}{j.offline && <span className="tag tag-gray" style={{ marginLeft: 6 }}>已下架</span>}</span>
              <span className="jc-salary" style={{ fontSize: 15 }}>{j.salary}</span>
            </div>
            <div className="jc-meta"><span className="tag tag-gray">{j.city}</span></div>
            <div className="jc-company"><span className="jc-logo">{j.company[0]}</span><span>{j.company}</span>
              <span className="grow" /><span className="tiny" style={{ color: 'var(--wx-red)' }} onClick={(e) => { e.stopPropagation(); toast('已取消收藏') }}>取消收藏</span></div>
          </div>
        ))}
      </div>
    </>
  )
}

/* ============ 浏览记录 ============ */
export function SeekerHistory() {
  const navigate = useNavigate()
  // mock 浏览历史：取 feedJobs 前 3 条标记为 viewed
  const history = feedJobs.filter(j => j.status === 'viewed' || j.status === 'chatted').slice(0, 6)
  return (
    <>
      <NavBar title="浏览记录" />
      <div className="page">
        {history.length === 0 ? (
          <div className="empty" style={{ paddingTop: 100, textAlign: 'center' }}><div className="tiny muted">暂无浏览记录</div></div>
        ) : (
          history.map((j, i) => (
            <div key={j.id} className="job-card" onClick={() => navigate('/seeker/job/' + j.id)}>
              <div className="jc-top">
                <span className="jc-name" style={{ fontSize: 15 }}>{j.name}</span>
                <span className="jc-salary" style={{ fontSize: 15 }}>{j.salary}</span>
              </div>
              <div className="jc-meta">
                <span className="tag tag-gray">{j.city}</span>
                <span className="tag tag-gray">{j.exp}</span>
                <span className="tag tag-green">匹配 {j.matchScore}%</span>
              </div>
              <div className="jc-company">
                <span className="jc-logo">{j.companyShow[0]}</span>
                <span>{j.companyShow}</span>
                <span className="grow" />
                <span className="tiny muted">{['今天 10:30', '昨天 15:20', '昨天 09:00', '6月1日', '5月30日', '5月28日'][i] || '较早'}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </>
  )
}

/* ============ A9: AI 面试准备 ============ */
export function SeekerInterviewPrep() {
  const p = interviewPrep
  return (
    <>
      <NavBar title="AI 面试准备" />
      <div className="page">
        <div style={{ background: 'linear-gradient(135deg,#07C160,#10AEFF)', color: '#fff', padding: '18px 16px' }}>
          <div style={{ fontSize: 17, fontWeight: 700 }}>{p.job}</div>
          <div style={{ fontSize: 13, opacity: .9, marginTop: 4 }}>{p.company} · {p.time}</div>
        </div>

        <AICard title="AI 企业速览" tip="帮你快速了解面试企业">{p.companyBrief}</AICard>

        <div className="cell-group-title">⚡ AI 预测高频面试问题</div>
        <div className="cell-group"><div style={{ padding: '8px 16px' }}>
          {p.commonQuestions.map((item, i) => (
            <div key={i} style={{ padding: '10px 0', borderBottom: i < p.commonQuestions.length - 1 ? '0.5px solid var(--wx-line-light)' : 'none' }}>
              <div style={{ fontWeight: 500, fontSize: 14 }}>Q{i + 1}. {item.q}</div>
              <div className="row gap6" style={{ marginTop: 4, alignItems: 'flex-start' }}>
                <span className="ai-badge soft" style={{ fontSize: 10, flexShrink: 0 }}>建议</span>
                <span className="tiny muted" style={{ lineHeight: 1.6 }}>{item.tip}</span>
              </div>
            </div>
          ))}
        </div></div>

        <div className="cell-group-title">💡 面试小贴士</div>
        <div className="cell-group"><div style={{ padding: 16, lineHeight: 2 }}>
          {p.tips.map((t, i) => <div key={i} className="tiny">• {t}</div>)}
        </div></div>

        <div className="ai-tip center" style={{ margin: '12px 16px' }}>⚡ 以上内容由 AI 基于岗位 JD 和你的简历画像生成，仅供参考</div>
      </div>
    </>
  )
}

/* ============ A1: 应聘者查看企业画像（只读） ============ */
export function SeekerCompanyView() {
  const navigate = useNavigate()
  const c = companyProfile
  return (
    <>
      <NavBar title="企业画像" />
      <div className="page">
        <div className="portrait-hd">
          <div className="ph-name">{c.name}</div>
          <span className="ph-level">⚡ AI 生成的企业画像</span>
        </div>
        <AICard title="AI 企业画像总结" tip="AI 基于企业信息与岗位数据生成">{c.oneline}</AICard>
        <div className="cell-group-title">企业标签</div>
        <div className="cell-group"><div style={{ padding: 16 }}>
          <div className="tagcloud">
            {c.tags.map(t => <span key={t.t} className={`tag ${({green:'tag-green',blue:'tag-blue',orange:'tag-orange'})[t.c]}`} style={{ fontSize: 13, padding: '5px 12px' }}>{t.t}</span>)}
          </div>
        </div></div>
        <div className="cell-group-title">企业维度评分</div>
        <div className="center" style={{ background: '#fff', paddingTop: 8 }}><RadarChart data={c.dims} size={240} color="#10AEFF" /></div>
        <div className="cell-group"><div style={{ padding: '14px 16px 4px' }}>
          {c.dims.map(d => <ScoreBar key={d.key} label={d.key} score={d.score} color={d.score >= 85 ? '#07C160' : '#FA9D3B'} />)}
        </div></div>
      </div>
    </>
  )
}

/* ============ 分享弹层（可复用） ============ */
export function ShareSheet({ title, onClose }) {
  const toast = useToast()
  const ch = [['💬', '微信好友'], ['🌅', '朋友圈'], ['🔗', '复制链接']]
  return (
    <Sheet title={title || '分享到'} onClose={onClose}>
      <div className="row" style={{ justifyContent: 'space-around', padding: '6px 0 16px' }}>
        {ch.map(([icon, label]) => (
          <div key={label} className="center" onClick={() => { toast('已' + (label === '复制链接' ? '复制' : '分享至' + label)); onClose() }}>
            <div style={{ width: 50, height: 50, borderRadius: '50%', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, margin: '0 auto 6px' }}>{icon}</div>
            <div className="tiny muted">{label}</div>
          </div>
        ))}
      </div>
    </Sheet>
  )
}
