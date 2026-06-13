import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, AIBadge, Sheet, useToast } from '../components/ui.jsx'
import { RecruiterBottomNav } from './RecruiterBottomNav.jsx'
import { talentPool, talentStats, getTalent, getCandidate, getTeamNotes, currentRecruiter, pickColor, resumeParsed } from '../mock/data.js'
import { listRecruiterApplications, updateApplicationStatus } from '../services/index.js'
import { applicationStatusTag, applicationStatusText, formatDateTime } from '../utils/applicationView.js'

function getTalentResume(t) {
  const candidate = getCandidate(t.id)
  const hasResume = candidate?.hasResume ?? ['active'].includes(t.status)
  if (!hasResume) return null

  const primaryJob = t.appliedJobs[0]?.jobName || candidate?.job || '目标岗位'
  const expTag = t.tags.find(tag => tag.includes('年')) || resumeParsed.exp
  return {
    ...resumeParsed,
    name: t.name,
    exp: expTag,
    targetJob: primaryJob,
    original: {
      fileName: `${t.name}_${primaryJob}_原始简历.pdf`,
      fileSize: t.virtual ? '1.8 MB' : '2.4 MB',
      uploadedAt: t.appliedJobs[0]?.date || t.lastActive,
      pages: 2,
      source: '候选人投递时上传',
    },
    skills: Array.from(new Set([...t.tags, ...resumeParsed.skills])).slice(0, 8),
    work: [
      {
        company: t.virtual ? '某科技公司' : resumeParsed.work[0].company,
        role: primaryJob.includes('产品') ? '产品经理' : primaryJob.includes('设计') ? 'UI设计师' : primaryJob.includes('Java') ? '后端工程师' : '前端工程师',
        period: resumeParsed.work[0].period,
        desc: t.tags.length ? `核心能力：${t.tags.slice(0, 3).join('、')}` : resumeParsed.work[0].desc,
      },
      ...resumeParsed.work.slice(1),
    ],
  }
}

/* ============ 人才池：以应聘者为中心的全量视图 ============ */
export function RecruiterTalentPool() {
  const navigate = useNavigate()
  const toast = useToast()
  const [filter, setFilter] = useState('all') // all | active | starred
  const [sortBy, setSortBy] = useState('match') // match | time | name
  const [selected, setSelected] = useState(new Set())
  const [showBatch, setShowBatch] = useState(false)
  const [applications, setApplications] = useState([])
  const [applicationsLoading, setApplicationsLoading] = useState(true)
  const [applicationsError, setApplicationsError] = useState('')
  const [updatingApplicationId, setUpdatingApplicationId] = useState(null)

  const loadApplications = () => {
    setApplicationsLoading(true)
    listRecruiterApplications({ limit: 100 })
      .then(data => {
        setApplications(data.items || [])
        setApplicationsError('')
      })
      .catch(error => {
        setApplications([])
        setApplicationsError(error.message || '投递列表加载失败')
      })
      .finally(() => setApplicationsLoading(false))
  }

  useEffect(() => {
    loadApplications()
  }, [])

  const changeApplicationStatus = async (applicationId, status) => {
    setUpdatingApplicationId(applicationId)
    try {
      await updateApplicationStatus(applicationId, {
        status,
        reject_reason: status === 'rejected' ? '暂不匹配当前岗位要求' : undefined,
      })
      toast('投递状态已更新')
      loadApplications()
    } catch (error) {
      toast(error.message || '状态更新失败')
    } finally {
      setUpdatingApplicationId(null)
    }
  }

  const statusLabel = { active: '活跃', passive: '一般', archived: '已归档' }
  const statusColor = { active: 'tag-green', passive: 'tag-orange', archived: 'tag-gray' }
  const emotionEmoji = { high: '🔥', medium: '💛', low: '🤍' }

  let list = [...talentPool]
  if (filter === 'active') list = list.filter(t => t.status === 'active')
  if (filter === 'starred') {
    // mock: 在真实场景中从用户标记数据读取，这里简化为匹配度>=80的
    list = list.filter(t => t.matchAvg >= 80)
  }
  if (sortBy === 'match') list.sort((a, b) => b.matchAvg - a.matchAvg)
  if (sortBy === 'time') list.sort((a, b) => (b.lastActive > a.lastActive ? 1 : -1))

  const toggle = (id) => setSelected(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })

  return (
    <>
      <NavBar title="人才池" right={<span style={{ color: 'var(--wx-green)', cursor: 'pointer' }} onClick={() => setShowBatch(true)}>批量操作</span>} />

      <div className="page has-tabbar" style={{ paddingBottom: 80 }}>
        {/* 总览统计 */}
        <div className="row" style={{ background: '#fff', padding: '14px 16px', gap: 0 }}>
          {[['总人才', talentStats.total], ['本月新增', talentStats.newThisMonth], ['活跃沟通', talentStats.activeChatting], ['已标记', talentStats.starred]].map(([k, v], i) => (
            <div key={i} className="grow center">
              <div style={{ fontSize: 20, fontWeight: 700 }}>{v}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{k}</div>
            </div>
          ))}
        </div>

        {/* 筛选 + 排序 */}
        <div className="row between padx" style={{ background: '#fff', padding: '8px 16px', borderTop: '0.5px solid var(--wx-line-light)', borderBottom: '0.5px solid var(--wx-line-light)' }}>
          <div className="row gap6">
            {[{ k: 'all', l: '全部' }, { k: 'active', l: '活跃' }, { k: 'starred', l: '高匹配' }].map(f => (
              <span key={f.k} className={`tag ${filter === f.k ? 'tag-green' : 'tag-gray'}`}
                style={{ cursor: 'pointer', fontSize: 12 }} onClick={() => setFilter(f.k)}>{f.l}</span>
            ))}
          </div>
          <div className="row gap6">
            {[{ k: 'match', l: '匹配度' }, { k: 'time', l: '最近活跃' }].map(s => (
              <span key={s.k} className={`tag ${sortBy === s.k ? 'tag-blue' : 'tag-gray'}`}
                style={{ cursor: 'pointer', fontSize: 12 }} onClick={() => setSortBy(s.k)}>{s.l}</span>
            ))}
          </div>
        </div>

        <div className="cell-group-title">真实投递管理</div>
        <div style={{ padding: '0 0 8px' }}>
          {applicationsLoading && (
            <div className="empty" style={{ padding: '24px 20px' }}><div className="tiny muted">正在加载真实投递...</div></div>
          )}
          {applicationsError && (
            <div className="ai-tip padx" style={{ marginTop: 8, color: 'var(--wx-red)' }}>{applicationsError}</div>
          )}
          {!applicationsLoading && !applicationsError && applications.length === 0 && (
            <div className="empty" style={{ padding: '24px 20px' }}><div className="tiny muted">暂无候选人投递</div></div>
          )}
          {!applicationsLoading && !applicationsError && applications.map(application => (
            <div key={application.id} className="job-card">
              <div className="row" style={{ gap: 10, alignItems: 'flex-start' }}>
                <span className="avatar" style={{ width: 40, height: 40, borderRadius: 8, background: pickColor(application.id), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, fontWeight: 600, flexShrink: 0 }}>
                  {(application.seeker_display_name || '候')[0]}
                </span>
                <div className="grow" style={{ minWidth: 0 }}>
                  <div className="row between">
                    <span style={{ fontWeight: 600, fontSize: 15 }}>{application.seeker_display_name || `候选人 #${application.seeker_id}`}</span>
                    <span className={`tag ${applicationStatusTag[application.status] || 'tag-gray'}`}>{applicationStatusText[application.status] || application.status}</span>
                  </div>
                  <div className="tiny muted" style={{ marginTop: 4 }}>
                    投递岗位：{application.job_title || `岗位 #${application.job_id}`} {application.job_city ? `· ${application.job_city}` : ''}
                  </div>
                  <div className="tiny muted" style={{ marginTop: 4 }}>投递时间：{formatDateTime(application.created_at)}</div>
                  {application.resume_snapshot && (
                    <div className="tiny" style={{ marginTop: 6, lineHeight: 1.6, color: 'var(--wx-text-2)' }}>{application.resume_snapshot}</div>
                  )}
                  {application.reject_reason && (
                    <div className="tiny" style={{ marginTop: 6, color: 'var(--wx-red)' }}>拒绝原因：{application.reject_reason}</div>
                  )}
                  <div className="row gap6" style={{ marginTop: 10, flexWrap: 'wrap' }}>
                    {[
                      ['viewed', '已查看'],
                      ['interview_invited', '邀面'],
                      ['rejected', '拒绝'],
                      ['hired', '录用'],
                    ].map(([status, label]) => (
                      <button
                        key={status}
                        className={`btn btn-sm ${application.status === status ? 'btn-disabled' : 'btn-default'}`}
                        disabled={updatingApplicationId === application.id || application.status === status}
                        onClick={() => changeApplicationStatus(application.id, status)}
                        style={{ flex: '0 0 auto' }}
                      >
                        {updatingApplicationId === application.id ? '处理中...' : label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 人才卡片列表 */}
        <div style={{ padding: '10px 0' }}>
          {list.map(t => (
            <div key={t.id} className="job-card" style={{ position: 'relative', cursor: 'pointer' }}
              onClick={() => navigate('/recruiter/talent/' + t.id)}>
              {selected.has(t.id) && <span style={{ position: 'absolute', top: 8, right: 12, color: 'var(--wx-green)', fontSize: 18 }}>☑</span>}
              <div className="row" style={{ gap: 10 }}>
                <span className="avatar" style={{ width: 44, height: 44, borderRadius: 8, background: pickColor(t.logoIdx), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 17, fontWeight: 600, flexShrink: 0 }}>{t.name[0]}</span>
                <div className="grow" style={{ overflow: 'hidden' }}>
                  <div className="row between">
                    <span style={{ fontWeight: 600, fontSize: 15 }}>{t.name}{t.virtual && <span className="tag tag-gray" style={{ marginLeft: 4, fontSize: 10 }}>虚拟</span>}</span>
                    <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--wx-green)' }}>{t.matchAvg}<span style={{ fontSize: 11, fontWeight: 400 }}>%</span></span>
                  </div>
                  <div className="row gap6" style={{ marginTop: 4, flexWrap: 'wrap' }}>
                    <span className={`tag ${statusColor[t.status]}`} style={{ fontSize: 10 }}>{statusLabel[t.status]} {emotionEmoji[t.emotion]}</span>
                    <span className={`tag ${getTalentResume(t) ? 'tag-blue' : 'tag-gray'}`} style={{ fontSize: 10, padding: '1px 6px' }}>
                      {getTalentResume(t) ? '简历已上传' : '未上传简历'}
                    </span>
                    {t.tags.slice(0, 3).map(tg => <span key={tg} className="tag tag-green" style={{ fontSize: 10, padding: '1px 6px' }}>{tg}</span>)}
                  </div>
                  <div className="row between tiny muted" style={{ marginTop: 4 }}>
                    <span>投递 {t.appliedJobs.length} 个岗位 · 浏览 {t.viewed} 次</span>
                    <span>{t.lastActive}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 批量操作浮层 */}
        {showBatch && (
          <div className="sheet-mask" onClick={() => setShowBatch(false)}>
            <div className="sheet" onClick={e => e.stopPropagation()} style={{ maxHeight: 300 }}>
              <div className="sheet-hd">批量操作</div>
              <div className="sheet-body" style={{ padding: '10px 16px 20px' }}>
                <div className="cell" onClick={() => { toast('已对选中人才打上"重点关注"标签'); setShowBatch(false) }}>
                  <span style={{ marginRight: 10 }}>🏷</span><span>打标签</span>
                </div>
                <div className="cell" onClick={() => { toast('测评链接已推送'); setShowBatch(false) }}>
                  <span style={{ marginRight: 10 }}>📋</span><span>推送测评</span>
                </div>
                <div className="cell" onClick={() => { toast('已批量发起沟通'); setShowBatch(false) }}>
                  <span style={{ marginRight: 10 }}>💬</span><span>批量邀请沟通</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      <RecruiterBottomNav />
    </>
  )
}

/* ============ 单个人才详情 ============ */
export function RecruiterTalentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const t = getTalent(id)
  const [notes, setNotes] = useState(getTeamNotes(id))
  const [noteInput, setNoteInput] = useState('')
  const [showOriginalResume, setShowOriginalResume] = useState(false)
  if (!t) return <><NavBar title="人才详情" /><div className="empty" style={{ paddingTop: 100 }}>人才信息不存在</div></>

  const statusLabel = { viewed: '已浏览', chatted: '已沟通', applied: '已投递' }
  const statusColor2 = { viewed: 'tag-gray', chatted: 'tag-green', applied: 'tag-blue' }
  const resume = getTalentResume(t)
  const originalResume = resume?.original

  const addNote = () => {
    if (!noteInput.trim()) return
    setNotes(ns => [...ns, { id: Date.now(), author: currentRecruiter, text: noteInput.trim(), time: '刚刚' }])
    setNoteInput('')
    toast('备注已添加，团队成员可见')
  }

  return (
    <>
      <NavBar title={t.name + (t.virtual ? '（虚拟名）' : '')}
        right={<span style={{ cursor: 'pointer' }} onClick={() => toast('已标记为重点关注')}>⭐</span>} />

      <div className="page">
        {/* 头部 */}
        <div className="row" style={{ background: '#fff', padding: '16px', gap: 12 }}>
          <span className="avatar" style={{ width: 52, height: 52, borderRadius: 10, background: pickColor(t.logoIdx), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 600 }}>{t.name[0]}</span>
          <div className="grow">
            <div className="row between">
              <span style={{ fontWeight: 600, fontSize: 16 }}>{t.name}</span>
              <span style={{ fontSize: 22, fontWeight: 800, color: 'var(--wx-green)' }}>{t.matchAvg}<span style={{ fontSize: 12, fontWeight: 400 }}>%</span></span>
            </div>
            <div className="row gap6" style={{ marginTop: 4, flexWrap: 'wrap' }}>
              {t.tags.map(tg => <span key={tg} className="tag tag-green" style={{ fontSize: 11 }}>{tg}</span>)}
              <span className="ai-badge soft" style={{ fontSize: 10 }}>AI匹配</span>
            </div>
            <div className="tiny muted" style={{ marginTop: 4 }}>最近活跃：{t.lastActive} · 总浏览 {t.viewed} 次</div>
          </div>
        </div>

        {/* 原始简历 */}
        <div className="cell-group-title">原始简历</div>
        {resume ? (
          <div className="cell-group">
            <div className="cell" style={{ alignItems: 'flex-start' }}>
              <span style={{ marginRight: 10, fontSize: 22 }}>📎</span>
              <div className="grow" style={{ overflow: 'hidden' }}>
                <div style={{ fontWeight: 600, fontSize: 14, wordBreak: 'break-all' }}>{originalResume.fileName}</div>
                <div className="tiny muted" style={{ marginTop: 4 }}>
                  PDF · {originalResume.fileSize} · {originalResume.pages}页 · {originalResume.uploadedAt}
                </div>
                <div className="tiny muted" style={{ marginTop: 2 }}>{originalResume.source}</div>
              </div>
            </div>
            <div style={{ padding: '0 16px 14px' }}>
              <div className="row gap8">
                <button className="btn btn-primary btn-sm" onClick={() => setShowOriginalResume(true)}>预览原件</button>
                <button className="btn btn-default btn-sm" onClick={() => toast('原始简历下载已开始（mock）')}>下载</button>
              </div>
            </div>
          </div>
        ) : (
          <div className="cell-group">
            <div className="cell">
              <span style={{ marginRight: 10, fontSize: 20 }}>📎</span>
              <span className="grow">该候选人暂未上传原始简历</span>
              <span className="tag tag-gray" style={{ fontSize: 11 }}>不可查看</span>
            </div>
          </div>
        )}

        {/* AI 解析摘要 */}
        <div className="cell-group-title">AI 解析摘要</div>
        {resume ? (
          <div className="cell-group">
            <div className="cell" style={{ alignItems: 'flex-start' }}>
              <span style={{ marginRight: 10, fontSize: 20 }}>📄</span>
              <div className="grow">
                <div className="row between">
                  <span style={{ fontWeight: 600 }}>{resume.name}的简历</span>
                  <AIBadge soft>AI解析</AIBadge>
                </div>
                <div className="tiny muted" style={{ marginTop: 4 }}>
                  {resume.edu} · {resume.exp} · 意向：{resume.targetJob}
                </div>
              </div>
              <span className="tag tag-blue" style={{ flexShrink: 0, marginLeft: 8, fontSize: 11 }}>已展示</span>
            </div>
            <div className="cell">
              <span className="cell-label">联系方式</span>
              <span className="cell-value">{resume.phone} · {resume.email}</span>
            </div>
            <div className="cell">
              <span className="cell-label">院校专业</span>
              <span className="cell-value">{resume.school} · {resume.major}</span>
            </div>
            <div style={{ padding: '12px 16px', borderTop: '0.5px solid var(--wx-line-light)' }}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>工作经历</div>
              {resume.work.map((w, i) => (
                <div key={i} style={{ padding: '8px 0', borderTop: i ? '0.5px solid var(--wx-line-light)' : 'none' }}>
                  <div className="row between">
                    <span style={{ fontSize: 13, fontWeight: 500 }}>{w.role} · {w.company}</span>
                    <span className="tiny muted">{w.period}</span>
                  </div>
                  <div className="tiny muted" style={{ marginTop: 3, lineHeight: 1.6 }}>{w.desc}</div>
                </div>
              ))}
            </div>
            <div style={{ padding: '12px 16px', borderTop: '0.5px solid var(--wx-line-light)' }}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>技能标签</div>
              <div className="tagcloud">
                {resume.skills.map(s => <span key={s} className="tag tag-green" style={{ fontSize: 12, padding: '3px 10px' }}>{s}</span>)}
              </div>
            </div>
          </div>
        ) : (
          <div className="cell-group">
            <div className="cell">
              <span style={{ marginRight: 10, fontSize: 20 }}>📄</span>
              <span className="grow">该候选人暂未上传简历</span>
              <span className="tag tag-gray" style={{ fontSize: 11 }}>不可查看</span>
            </div>
          </div>
        )}

        {/* 投递的岗位 */}
        <div className="cell-group-title">投递/互动的岗位（{t.appliedJobs.length}）</div>
        <div className="cell-group">
          {t.appliedJobs.map(j => (
            <div key={j.jobId} className="cell" onClick={() => navigate('/recruiter/stats')}>
              <span className="grow" style={{ fontWeight: 500, fontSize: 14 }}>{j.jobName}</span>
              <span className={`tag ${statusColor2[j.status]}`} style={{ fontSize: 11 }}>{statusLabel[j.status]}</span>
              <span className="tiny muted" style={{ marginLeft: 8 }}>{j.date}</span>
            </div>
          ))}
        </div>

        {/* 互动时间线 */}
        <div className="cell-group-title">互动记录</div>
        <div className="cell-group">
          <div style={{ padding: 14, lineHeight: 2 }}>
            <div className="tiny">📅 {t.appliedJobs[0]?.date} 浏览岗位「{t.appliedJobs[0]?.jobName}」</div>
            <div className="tiny">💬 {t.lastActive} 最后留言互动</div>
            {t.emotion === 'high' && <div className="tiny" style={{ color: 'var(--wx-green-dark)' }}>🔥 AI 判定：高意向候选人</div>}
          </div>
        </div>

        {/* 团队协作备注 */}
        <div className="cell-group-title row between" style={{ paddingRight: 16 }}>
          <span>👥 团队备注</span>
          <span className="tiny muted">团队成员共享可见</span>
        </div>
        <div className="cell-group">
          <div style={{ padding: '8px 16px' }}>
            {notes.length === 0 ? (
              <div className="tiny muted" style={{ padding: '8px 0', textAlign: 'center' }}>还没有团队备注，添加一条让同事看到</div>
            ) : (
              notes.map(n => (
                <div key={n.id} style={{ padding: '10px 0', borderBottom: '0.5px solid var(--wx-line-light)' }}>
                  <div className="row between">
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--wx-green-dark)' }}>{n.author}</span>
                    <span className="tiny muted">{n.time}</span>
                  </div>
                  <div className="tiny" style={{ marginTop: 3, lineHeight: 1.6 }}>{n.text}</div>
                </div>
              ))
            )}
            <div className="row gap8" style={{ marginTop: 10 }}>
              <input className="grow" value={noteInput} placeholder="添加团队备注（如：电话初筛通过…）"
                onChange={e => setNoteInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && addNote()}
                style={{ background: 'var(--wx-surface-2)', borderRadius: 8, padding: '8px 12px', fontSize: 13 }} />
              <button className="btn btn-weak btn-sm" onClick={addNote} style={{ flexShrink: 0 }}>添加</button>
            </div>
          </div>
        </div>

        {/* 操作区 */}
        <div className="btn-block-wrap" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <button
            className={`btn ${resume ? 'btn-weak' : 'btn-default'}`}
            onClick={() => resume ? setShowOriginalResume(true) : toast('候选人暂未上传简历')}
          >
            📎 原始简历
          </button>
          <button className="btn btn-default" onClick={() => navigate('/recruiter/chat/' + (t.id <= 3 ? t.id : 1))}>💬 发起沟通</button>
          <button className="btn btn-default" onClick={() => toast('测评链接已推送')}>📋 推送测评</button>
          <button className="btn btn-primary" onClick={() => toast('已推荐给合作伙伴')}>📤 转发推荐</button>
        </div>
      </div>
      {showOriginalResume && originalResume && (
        <Sheet title="原始简历预览" onClose={() => setShowOriginalResume(false)}>
          <div style={{ background: '#F2F3F5', padding: 12, borderRadius: 10 }}>
            <div className="row between" style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{originalResume.fileName}</div>
              <span className="tag tag-blue" style={{ fontSize: 11 }}>PDF</span>
            </div>
            <div style={{
              background: '#fff',
              border: '1px solid var(--wx-line)',
              boxShadow: '0 2px 10px rgba(0,0,0,0.08)',
              padding: 18,
              minHeight: 430,
              color: '#222',
              fontSize: 12,
              lineHeight: 1.7,
            }}>
              <div className="row between" style={{ borderBottom: '1px solid #222', paddingBottom: 8, marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1.2 }}>{resume.name}</div>
                  <div style={{ color: '#666', marginTop: 4 }}>{resume.targetJob} · {resume.exp}</div>
                </div>
                <div style={{ textAlign: 'right', color: '#555' }}>
                  <div>{resume.phone}</div>
                  <div>{resume.email}</div>
                </div>
              </div>
              <div style={{ fontWeight: 700, marginTop: 10 }}>教育背景</div>
              <div>{resume.school} · {resume.major} · {resume.edu}</div>
              <div style={{ fontWeight: 700, marginTop: 12 }}>工作经历</div>
              {resume.work.map((w, i) => (
                <div key={i} style={{ marginTop: 8 }}>
                  <div className="row between">
                    <span style={{ fontWeight: 600 }}>{w.company} · {w.role}</span>
                    <span style={{ color: '#666' }}>{w.period}</span>
                  </div>
                  <div style={{ color: '#444' }}>{w.desc}</div>
                </div>
              ))}
              <div style={{ fontWeight: 700, marginTop: 12 }}>核心技能</div>
              <div>{resume.skills.join(' / ')}</div>
              <div style={{ marginTop: 18, borderTop: '1px dashed #ccc', paddingTop: 8, color: '#999', fontSize: 11 }}>
                第 1 / {originalResume.pages} 页 · 原始简历预览 mock
              </div>
            </div>
            <div className="row gap8" style={{ marginTop: 12 }}>
              <button className="btn btn-default" onClick={() => toast('已切换到第2页（mock）')}>下一页</button>
              <button className="btn btn-primary" onClick={() => toast('原始简历下载已开始（mock）')}>下载原件</button>
            </div>
          </div>
        </Sheet>
      )}
      <RecruiterBottomNav />
    </>
  )
}
