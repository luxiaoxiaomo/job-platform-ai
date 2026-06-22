import React, { useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { Cell, CellGroup, NavBar, AIBadge, Sheet, useToast } from '../components/ui.jsx'
import { RecruiterBottomNav } from './RecruiterBottomNav.jsx'
import { talentPool, talentStats, getTalent, getCandidate, getTeamNotes, currentRecruiter, pickColor, resumeParsed } from '../mock/data.js'
import {
  fetchRecruiterApplicationResumeFile,
  getRecruiterApplication,
  getRecruiterApplicationMatch,
  getRecruiterApplicationStructuredProfile,
  listPublicTagLibraryItems,
  listMyConversations,
  listRecruiterApplications,
  searchResumes,
  updateApplicationStatus,
} from '../services/index.js'
import { applicationStatusTag, applicationStatusText, formatDateTime } from '../utils/applicationView.js'
import { pickPublicTagNames, usePublicTagOptions } from '../common/usePublicTagOptions.js'

function getTalentResume(t, tagOptions = []) {
  const candidate = getCandidate(t.id)
  const hasResume = candidate?.hasResume ?? ['active'].includes(t.status)
  if (!hasResume) return null

  const primaryJob = t.appliedJobs[0]?.jobName || candidate?.job || '目标岗位'
  const publicTagNames = pickPublicTagNames(tagOptions, t.id, 5)
  return {
    ...resumeParsed,
    name: t.name,
    exp: resumeParsed.exp,
    targetJob: primaryJob,
    original: {
      fileName: `${t.name}_${primaryJob}_原始简历.pdf`,
      fileSize: t.virtual ? '1.8 MB' : '2.4 MB',
      uploadedAt: t.appliedJobs[0]?.date || t.lastActive,
      pages: 2,
      source: '候选人投递时上传',
    },
    skills: publicTagNames,
    work: [
      {
        company: t.virtual ? '某科技公司' : resumeParsed.work[0].company,
        role: primaryJob.includes('产品') ? '产品经理' : primaryJob.includes('设计') ? 'UI设计师' : primaryJob.includes('Java') ? '后端工程师' : '前端工程师',
        period: resumeParsed.work[0].period,
        desc: publicTagNames.length ? `核心能力：${publicTagNames.slice(0, 3).join('、')}` : resumeParsed.work[0].desc,
      },
      ...resumeParsed.work.slice(1),
    ],
  }
}

/* ============ 人才池：以应聘者为中心的全量视图 ============ */
export function RecruiterTalentPool() {
  const navigate = useNavigate()
  const toast = useToast()
  const [mode, setMode] = useState('applications') // applications | demo
  const [filter, setFilter] = useState('all') // all | active | starred
  const [sortBy, setSortBy] = useState('match') // match | time | name
  const [selected, setSelected] = useState(new Set())
  const [showBatch, setShowBatch] = useState(false)
  const [applications, setApplications] = useState([])
  const [applicationsLoading, setApplicationsLoading] = useState(true)
  const [applicationsError, setApplicationsError] = useState('')
  const [updatingApplicationId, setUpdatingApplicationId] = useState(null)
  const [tagOptions, setTagOptions] = useState([])
  const [selectedTagId, setSelectedTagId] = useState('')
  const [tagOptionsLoading, setTagOptionsLoading] = useState(false)
  const [resumeResults, setResumeResults] = useState([])
  const [resumeSearchLoading, setResumeSearchLoading] = useState(false)
  const [resumeSearchError, setResumeSearchError] = useState('')

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

  useEffect(() => {
    let alive = true
    setTagOptionsLoading(true)
    listPublicTagLibraryItems({ limit: 100 })
      .then(data => {
        if (alive) setTagOptions(data.items || [])
      })
      .catch(() => {
        if (alive) setTagOptions([])
      })
      .finally(() => {
        if (alive) setTagOptionsLoading(false)
      })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    if (!selectedTagId) {
      setResumeResults([])
      setResumeSearchError('')
      return undefined
    }
    const selectedTag = tagOptions.find(item => String(item.id) === String(selectedTagId))
    let alive = true
    setResumeSearchLoading(true)
    setResumeSearchError('')
    searchResumes({ q: selectedTag?.name || '候选人', tag_id: selectedTagId, limit: 50 })
      .then(data => {
        if (alive) setResumeResults(data.items || [])
      })
      .catch(error => {
        if (!alive) return
        setResumeResults([])
        setResumeSearchError(error.message || '标签筛选候选人失败')
      })
      .finally(() => {
        if (alive) setResumeSearchLoading(false)
      })
    return () => { alive = false }
  }, [selectedTagId, tagOptions])

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

        <div className="row between padx" style={{ background: '#fff', padding: '10px 16px', borderTop: '0.5px solid var(--wx-line-light)', borderBottom: '0.5px solid var(--wx-line-light)' }}>
          <div className="row gap6">
            {[{ k: 'applications', l: '真实投递' }, { k: 'demo', l: '演示人才池' }].map(item => (
              <span
                key={item.k}
                className={`tag ${mode === item.k ? 'tag-green' : 'tag-gray'}`}
                style={{ cursor: 'pointer', fontSize: 12 }}
                onClick={() => setMode(item.k)}
              >
                {item.l}
              </span>
            ))}
          </div>
        </div>

        {mode === 'applications' && (
          <>
            <div className="cell-group-title">候选人标签筛选</div>
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
                  {tagOptions.slice(0, 16).map(item => (
                    <span
                      key={item.id}
                      className={`tag ${String(selectedTagId) === String(item.id) ? 'tag-green' : 'tag-gray'}`}
                      style={{ cursor: 'pointer', fontSize: 12 }}
                      onClick={() => setSelectedTagId(String(item.id))}
                    >
                      {item.name}
                    </span>
                  ))}
                  {tagOptionsLoading && <span className="tiny muted">标签加载中...</span>}
                </div>
              </div>
            </div>
            {selectedTagId && (
              <>
                <div className="cell-group-title">标签匹配候选人</div>
                <div style={{ padding: '0 0 8px' }}>
                  {resumeSearchLoading && (
                    <div className="empty" style={{ padding: '20px' }}><div className="tiny muted">正在按标签搜索候选人...</div></div>
                  )}
                  {resumeSearchError && (
                    <div className="ai-tip padx" style={{ marginTop: 8, color: 'var(--wx-red)' }}>{resumeSearchError}</div>
                  )}
                  {!resumeSearchLoading && !resumeSearchError && resumeResults.length === 0 && (
                    <div className="empty" style={{ padding: '20px' }}><div className="tiny muted">暂无匹配该标签的候选人</div></div>
                  )}
                  {!resumeSearchLoading && !resumeSearchError && resumeResults.map(item => (
                    <div key={item.structured_profile_id || item.seeker_id} className="job-card">
                      <div className="row" style={{ gap: 10, alignItems: 'flex-start' }}>
                        <span className="avatar" style={{ width: 40, height: 40, borderRadius: 8, background: pickColor(item.seeker_id), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, fontWeight: 600, flexShrink: 0 }}>
                          {(item.real_name || item.seeker_display_name || '候')[0]}
                        </span>
                        <div className="grow" style={{ minWidth: 0 }}>
                          <div className="row between">
                            <span style={{ fontWeight: 600, fontSize: 15 }}>{item.real_name || item.seeker_display_name || `候选人 #${item.seeker_id}`}</span>
                            <span className="tag tag-blue">{Math.round(item.score || 0)} 分</span>
                          </div>
                          <div className="tiny muted" style={{ marginTop: 4 }}>
                            {[item.target_position, item.current_city, item.highest_education, item.work_years !== null && item.work_years !== undefined ? `${item.work_years}年经验` : ''].filter(Boolean).join(' / ')}
                          </div>
                          <div className="row gap6" style={{ marginTop: 8, flexWrap: 'wrap' }}>
                            {(item.tag_refs || []).map(tag => (
                              <span key={tag.id} className="tag tag-green" style={{ fontSize: 10, padding: '1px 6px' }}>{tag.name}</span>
                            ))}
                            {(item.skills || []).slice(0, 4).map(skill => (
                              <span key={skill} className="tag tag-gray" style={{ fontSize: 10, padding: '1px 6px' }}>{skill}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
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
                <div
                  key={application.id}
                  className="job-card"
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate('/recruiter/applications/' + application.id, { state: { application } })}
                >
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
                      {application.resume_file_name && (
                        <div className="tiny" style={{ marginTop: 6, color: 'var(--wx-green-dark)' }}>
                          简历文件：{application.resume_file_name}
                        </div>
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
                            onClick={(event) => {
                              event.stopPropagation()
                              changeApplicationStatus(application.id, status)
                            }}
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
          </>
        )}

        {mode === 'demo' && (
          <>
            <div className="cell-group-title">演示人才池（Mock 数据）</div>
            <div className="ai-tip" style={{ marginTop: 0 }}>
              以下卡片仍是原型演示数据，不来自数据库投递记录；真实投递请切回上方“真实投递”。
            </div>
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
                        <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--wx-green)' }}>{t.matchAvg}<span style={{ fontSize: 11, fontWeight: 400 }}>%</span><span className="tag tag-gray" style={{ marginLeft: 4, fontSize: 10 }}>演示</span></span>
                      </div>
                      <div className="row gap6" style={{ marginTop: 4, flexWrap: 'wrap' }}>
                        <span className={`tag ${statusColor[t.status]}`} style={{ fontSize: 10 }}>{statusLabel[t.status]} {emotionEmoji[t.emotion]}</span>
                        <span className={`tag ${getTalentResume(t, tagOptions) ? 'tag-blue' : 'tag-gray'}`} style={{ fontSize: 10, padding: '1px 6px' }}>
                          {getTalentResume(t, tagOptions) ? '简历已上传' : '未上传简历'}
                        </span>
                        {pickPublicTagNames(tagOptions, t.id, 3).length > 0
                          ? pickPublicTagNames(tagOptions, t.id, 3).map(tg => <span key={tg} className="tag tag-green" style={{ fontSize: 10, padding: '1px 6px' }}>{tg}</span>)
                          : <span className="tiny muted">{tagOptionsLoading ? '标签加载中...' : '暂无标签库标签'}</span>}
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
          </>
        )}

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

export function RecruiterApplicationDetail() {
  const { applicationId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const toast = useToast()
  const [application, setApplication] = useState(location.state?.application || null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updating, setUpdating] = useState(false)
  const [fileLoading, setFileLoading] = useState(false)
  const [conversation, setConversation] = useState(null)
  const [conversationLoading, setConversationLoading] = useState(false)
  const [matchResult, setMatchResult] = useState(null)
  const [matchLoading, setMatchLoading] = useState(false)
  const [matchError, setMatchError] = useState('')
  const [profileDetail, setProfileDetail] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)
  const [profileError, setProfileError] = useState('')

  const loadApplication = () => {
    setLoading(true)
    getRecruiterApplication(applicationId)
      .then(data => {
        setApplication(data)
        setError('')
      })
      .catch(err => {
        setError(err.message || '投递详情加载失败')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadApplication()
  }, [applicationId])

  useEffect(() => {
    if (!applicationId) return undefined
    let alive = true
    setMatchLoading(true)
    setMatchError('')
    getRecruiterApplicationMatch(applicationId)
      .then(data => {
        if (!alive) return
        setMatchResult(data)
      })
      .catch(err => {
        if (!alive) return
        setMatchResult(null)
        setMatchError(err.message || '匹配结果暂不可用')
      })
      .finally(() => {
        if (alive) setMatchLoading(false)
      })
    return () => { alive = false }
  }, [applicationId])

  useEffect(() => {
    if (!applicationId) return undefined
    let alive = true
    setProfileLoading(true)
    setProfileError('')
    getRecruiterApplicationStructuredProfile(applicationId)
      .then(data => {
        if (!alive) return
        setProfileDetail(data)
      })
      .catch(err => {
        if (!alive) return
        setProfileDetail(null)
        setProfileError(err.message || '结构化画像暂不可用')
      })
      .finally(() => {
        if (alive) setProfileLoading(false)
      })
    return () => { alive = false }
  }, [applicationId])

  useEffect(() => {
    if (!application?.job_id || !application?.seeker_id) return undefined
    let alive = true
    setConversationLoading(true)
    listMyConversations({ limit: 100 })
      .then(data => {
        if (!alive) return
        const matched = (data.items || []).find(item =>
          String(item.job_id) === String(application.job_id) &&
          String(item.seeker_id) === String(application.seeker_id)
        )
        setConversation(matched || null)
      })
      .catch(() => {
        if (alive) setConversation(null)
      })
      .finally(() => {
        if (alive) setConversationLoading(false)
      })
    return () => { alive = false }
  }, [application?.job_id, application?.seeker_id])

  const changeStatus = async (status) => {
    setUpdating(true)
    try {
      await updateApplicationStatus(applicationId, {
        status,
        reject_reason: status === 'rejected' ? '暂不匹配当前岗位要求' : undefined,
      })
      toast('投递状态已更新')
      loadApplication()
    } catch (err) {
      toast(err.message || '状态更新失败')
    } finally {
      setUpdating(false)
    }
  }

  const openResumeFile = async (mode) => {
    setFileLoading(true)
    try {
      const { blob, fileName } = await fetchRecruiterApplicationResumeFile(applicationId)
      const url = URL.createObjectURL(blob)
      if (mode === 'download') {
        const link = document.createElement('a')
        link.href = url
        link.download = application?.resume_file_name || fileName
        document.body.appendChild(link)
        link.click()
        link.remove()
      } else {
        window.open(url, '_blank', 'noopener,noreferrer')
      }
      setTimeout(() => URL.revokeObjectURL(url), 30000)
    } catch (err) {
      toast(err.message || '简历文件获取失败')
    } finally {
      setFileLoading(false)
    }
  }

  const timeline = application?.timeline || []
  const statusText = applicationStatusText[application?.status] || application?.status || '未知'
  const statusTag = applicationStatusTag[application?.status] || 'tag-gray'
  const actorText = { seeker: '求职者', recruiter: '招聘者', system: '系统' }
  const exchange = conversation?.contact_exchange
  const exchangeText = exchange?.status === 'accepted'
    ? '已交换联系方式'
    : exchange?.status === 'pending'
      ? '联系方式交换待确认'
      : exchange?.status === 'declined'
        ? '联系方式交换已拒绝'
        : '未交换联系方式'

  return (
    <>
      <NavBar title="投递详情" />
      <div className="page">
        {loading && !application && (
          <div className="empty" style={{ padding: '60px 20px' }}>
            <div className="tiny muted">正在加载投递详情...</div>
          </div>
        )}

        {error && (
          <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>
        )}

        {application && (
          <>
            <div className="job-card">
              <div className="row between" style={{ alignItems: 'flex-start', gap: 12 }}>
                <div className="grow" style={{ minWidth: 0 }}>
                  <div className="row gap8" style={{ alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontWeight: 700, fontSize: 18 }}>{application.seeker_display_name || `候选人 #${application.seeker_id}`}</span>
                    <span className={`tag ${statusTag}`}>{statusText}</span>
                  </div>
                  <div className="tiny muted" style={{ marginTop: 6 }}>
                    投递岗位：{application.job_title || `岗位 #${application.job_id}`} {application.job_city ? `· ${application.job_city}` : ''}
                  </div>
                  <div className="tiny muted" style={{ marginTop: 4 }}>
                    投递时间：{formatDateTime(application.created_at)}
                  </div>
                </div>
              </div>
              <div className="ai-tip" style={{ marginTop: 10 }}>
                当前页面展示数据库中的真实投递记录、简历快照、状态时间线和沟通状态。AI 匹配分与结构化简历画像后续接入。
              </div>
            </div>

            <div className="cell-group-title">投递简历</div>
            <div className="cell-group">
              <div className="cell" style={{ alignItems: 'flex-start' }}>
                <span style={{ marginRight: 10, fontSize: 22 }}>📄</span>
                <div className="grow" style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 600, wordBreak: 'break-all' }}>{application.resume_file_name || '未记录简历文件名'}</div>
                  {application.resume_snapshot && (
                    <div className="tiny" style={{ marginTop: 6, color: 'var(--wx-text-2)', lineHeight: 1.6 }}>
                      {application.resume_snapshot}
                    </div>
                  )}
                </div>
              </div>
              <div style={{ padding: '0 16px 14px' }}>
                <div className="row gap8">
                  <button className="btn btn-weak btn-sm" disabled={fileLoading} onClick={() => openResumeFile('preview')}>
                    {fileLoading ? '读取中...' : '预览原件'}
                  </button>
                  <button className="btn btn-default btn-sm" disabled={fileLoading} onClick={() => openResumeFile('download')}>
                    下载原件
                  </button>
                </div>
              </div>
            </div>

            {application.cover_message && (
              <>
                <div className="cell-group-title">求职者留言</div>
                <div className="cell-group">
                  <div style={{ padding: '12px 16px', fontSize: 14, lineHeight: 1.7 }}>{application.cover_message}</div>
                </div>
              </>
            )}

            <div className="cell-group-title">解析与匹配状态</div>
            <CellGroup>
              <Cell label="简历结构化解析" value={profileLoading ? '加载中...' : profileDetail ? '已生成结构化画像' : (profileError || '结构化画像暂不可用')} />
              <Cell label="AI 匹配分" value={matchLoading ? '计算中...' : matchResult ? `${matchResult.overall_score}分 · ${matchResult.recommendation}` : (matchError || '匹配结果暂不可用')} />
              <Cell label="数据来源" value="job_applications / jobs / users / job_application_timelines" />
            </CellGroup>
            {profileDetail && (
              <div className="cell-group" style={{ marginTop: 8 }}>
                <div style={{ padding: 16 }}>
                  <div style={{ fontWeight: 700, marginBottom: 8 }}>结构化简历画像</div>
                  {profileDetail.basic_info && (
                    <div className="tiny muted" style={{ lineHeight: 1.8 }}>
                      {[
                        profileDetail.basic_info.real_name,
                        profileDetail.basic_info.gender,
                        profileDetail.basic_info.age ? `${profileDetail.basic_info.age}岁` : '',
                        profileDetail.basic_info.highest_education,
                        profileDetail.basic_info.work_years !== null && profileDetail.basic_info.work_years !== undefined ? `${profileDetail.basic_info.work_years}年经验` : '',
                        profileDetail.basic_info.current_city,
                        profileDetail.basic_info.target_position,
                      ].filter(Boolean).join(' / ')}
                    </div>
                  )}
                  {profileDetail.skills?.length > 0 && (
                    <div className="row gap8" style={{ flexWrap: 'wrap', marginTop: 10 }}>
                      {profileDetail.skills.slice(0, 12).map(skill => (
                        <span key={skill.id || skill.skill_name} className="tag tag-green" style={{ fontSize: 11 }}>{skill.skill_name}</span>
                      ))}
                    </div>
                  )}
                  {profileDetail.educations?.length > 0 && (
                    <div style={{ marginTop: 12 }}>
                      <div className="tiny" style={{ fontWeight: 700 }}>教育经历</div>
                      {profileDetail.educations.slice(0, 2).map(item => (
                        <div key={item.id} className="tiny muted" style={{ marginTop: 4 }}>
                          {[item.school_name, item.major, item.degree, item.start_date && item.end_date ? `${item.start_date}-${item.end_date}` : ''].filter(Boolean).join(' / ')}
                        </div>
                      ))}
                    </div>
                  )}
                  {profileDetail.work_experiences?.length > 0 && (
                    <div style={{ marginTop: 12 }}>
                      <div className="tiny" style={{ fontWeight: 700 }}>工作经历</div>
                      {profileDetail.work_experiences.slice(0, 2).map(item => (
                        <div key={item.id} className="tiny muted" style={{ marginTop: 4 }}>
                          {[item.company_name, item.position, item.start_date && item.end_date ? `${item.start_date}-${item.end_date}` : ''].filter(Boolean).join(' / ')}
                        </div>
                      ))}
                    </div>
                  )}
                  {profileDetail.projects?.length > 0 && (
                    <div style={{ marginTop: 12 }}>
                      <div className="tiny" style={{ fontWeight: 700 }}>项目经历</div>
                      {profileDetail.projects.slice(0, 2).map(item => (
                        <div key={item.id} className="tiny muted" style={{ marginTop: 4 }}>
                          {[item.project_name, item.role].filter(Boolean).join(' / ')}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
            {matchResult && (
              <div className="cell-group" style={{ marginTop: 8 }}>
                <div style={{ padding: 16 }}>
                  <div className="row between" style={{ marginBottom: 10 }}>
                    <div>
                      <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--wx-green)' }}>{matchResult.overall_score}<span style={{ fontSize: 13, fontWeight: 500 }}> 分</span></div>
                      <div className="tiny muted">{matchResult.summary}</div>
                    </div>
                    <span className={`tag ${matchResult.level === 'high' ? 'tag-green' : matchResult.level === 'medium' ? 'tag-orange' : 'tag-red'}`}>{matchResult.recommendation}</span>
                  </div>
                  {(matchResult.dimensions || []).map(item => (
                    <div key={item.key} style={{ marginTop: 10 }}>
                      <div className="row between tiny" style={{ marginBottom: 4 }}>
                        <span>{item.label}</span>
                        <span>{item.score} 分 / 权重 {item.effective_weight}%</span>
                      </div>
                      <div style={{ height: 6, borderRadius: 999, background: '#EEF0F2', overflow: 'hidden' }}>
                        <div style={{ width: `${item.score}%`, height: '100%', background: item.score >= 80 ? 'var(--wx-green)' : item.score >= 60 ? 'var(--wx-orange)' : 'var(--wx-red)' }} />
                      </div>
                      <div className="tiny muted" style={{ marginTop: 4 }}>{item.explanation}</div>
                    </div>
                  ))}
                  {(matchResult.highlights?.length || matchResult.gaps?.length) ? (
                    <div className="ai-tip" style={{ marginTop: 12 }}>
                      {matchResult.highlights?.length ? <div>亮点：{matchResult.highlights.join('；')}</div> : null}
                      {matchResult.gaps?.length ? <div style={{ marginTop: 4 }}>缺口：{matchResult.gaps.join('；')}</div> : null}
                    </div>
                  ) : null}
                </div>
              </div>
            )}

            <div className="cell-group-title">状态时间线</div>
            <div className="cell-group">
              {timeline.length === 0 && (
                <div className="cell">
                  <span className="grow tiny muted">暂无状态记录</span>
                </div>
              )}
              {timeline.map(item => (
                <div key={item.id} className="cell" style={{ alignItems: 'flex-start' }}>
                  <span style={{ width: 8, height: 8, borderRadius: 999, background: 'var(--wx-green)', margin: '7px 12px 0 2px', flexShrink: 0 }} />
                  <div className="grow">
                    <div style={{ fontWeight: 600, fontSize: 14 }}>
                      {applicationStatusText[item.to_status] || item.to_status}
                    </div>
                    <div className="tiny muted" style={{ marginTop: 3 }}>
                      {formatDateTime(item.created_at)} · {actorText[item.actor_role] || item.actor_role || '系统'}
                    </div>
                    {item.note && <div className="tiny" style={{ marginTop: 3, color: 'var(--wx-text-2)' }}>{item.note}</div>}
                  </div>
                </div>
              ))}
            </div>

            {application.reject_reason && (
              <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>
                拒绝原因：{application.reject_reason}
              </div>
            )}

            <div className="cell-group-title">沟通状态</div>
            <CellGroup>
              <Cell label="会话" value={conversationLoading ? '加载中...' : conversation ? '已开始' : '未开始'} />
              <Cell label="联系方式交换" value={conversationLoading ? '加载中...' : exchangeText} />
            </CellGroup>
            {conversation && (
              <div className="btn-block-wrap">
                <button className="btn btn-weak" onClick={() => navigate('/recruiter/chat/' + conversation.id)}>打开会话</button>
              </div>
            )}

            <div className="btn-block-wrap row gap8" style={{ flexWrap: 'wrap' }}>
              {[
                ['viewed', '标记已查看'],
                ['interview_invited', '邀约面试'],
                ['rejected', '拒绝'],
                ['hired', '录用'],
              ].map(([status, label]) => (
                <button
                  key={status}
                  className={`btn btn-sm ${application.status === status ? 'btn-disabled' : status === 'interview_invited' ? 'btn-primary' : 'btn-default'}`}
                  disabled={updating || application.status === status}
                  onClick={() => changeStatus(status)}
                >
                  {updating ? '处理中...' : label}
                </button>
              ))}
            </div>

            <div className="btn-block-wrap">
              <button className="btn btn-default" onClick={() => navigate('/recruiter/talent')}>返回人才池</button>
            </div>
          </>
        )}
      </div>
    </>
  )
}

function LegacyRecruiterApplicationDetail() {
  const { applicationId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const toast = useToast()
  const [application, setApplication] = useState(location.state?.application || null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updating, setUpdating] = useState(false)
  const [fileLoading, setFileLoading] = useState(false)
  const [conversation, setConversation] = useState(null)
  const [conversationLoading, setConversationLoading] = useState(false)

  const loadApplication = () => {
    setLoading(true)
    getRecruiterApplication(applicationId)
      .then(data => {
        setApplication(data)
        setError('')
      })
      .catch(err => {
        setError(err.message || '投递详情加载失败')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadApplication()
  }, [applicationId])

  useEffect(() => {
    if (!application?.job_id || !application?.seeker_id) return undefined
    let alive = true
    setConversationLoading(true)
    listMyConversations({ limit: 100 })
      .then(data => {
        if (!alive) return
        const matched = (data.items || []).find(item =>
          String(item.job_id) === String(application.job_id) &&
          String(item.seeker_id) === String(application.seeker_id)
        )
        setConversation(matched || null)
      })
      .catch(() => {
        if (alive) setConversation(null)
      })
      .finally(() => {
        if (alive) setConversationLoading(false)
      })
    return () => { alive = false }
  }, [application?.job_id, application?.seeker_id])

  const changeStatus = async (status) => {
    setUpdating(true)
    try {
      await updateApplicationStatus(applicationId, {
        status,
        reject_reason: status === 'rejected' ? '暂不匹配当前岗位要求' : undefined,
      })
      toast('投递状态已更新')
      loadApplication()
    } catch (err) {
      toast(err.message || '状态更新失败')
    } finally {
      setUpdating(false)
    }
  }

  const openResumeFile = async (mode) => {
    setFileLoading(true)
    try {
      const { blob, fileName } = await fetchRecruiterApplicationResumeFile(applicationId)
      const url = URL.createObjectURL(blob)
      if (mode === 'download') {
        const link = document.createElement('a')
        link.href = url
        link.download = application?.resume_file_name || fileName
        document.body.appendChild(link)
        link.click()
        link.remove()
      } else {
        window.open(url, '_blank', 'noopener,noreferrer')
      }
      setTimeout(() => URL.revokeObjectURL(url), 30000)
    } catch (err) {
      toast(err.message || '简历文件获取失败')
    } finally {
      setFileLoading(false)
    }
  }

  const timeline = application?.timeline || []
  const statusText = applicationStatusText[application?.status] || application?.status || '未知'
  const statusTag = applicationStatusTag[application?.status] || 'tag-gray'
  const exchange = conversation?.contact_exchange
  const exchangeText = exchange?.status === 'accepted'
    ? 'Contacts exchanged'
    : exchange?.status === 'pending'
      ? 'Contact exchange pending'
      : exchange?.status === 'declined'
        ? 'Contact exchange declined'
        : 'No contact exchange'

  return (
    <>
      <NavBar title="投递详情" />
      <div className="page">
        {loading && !application && (
          <div className="empty" style={{ padding: '60px 20px' }}>
            <div className="tiny muted">正在加载投递详情...</div>
          </div>
        )}

        {error && (
          <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>
        )}

        {application && (
          <>
            <div className="job-card">
              <div className="row between" style={{ alignItems: 'flex-start', gap: 12 }}>
                <div className="grow" style={{ minWidth: 0 }}>
                  <div className="row gap8" style={{ alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontWeight: 700, fontSize: 18 }}>{application.seeker_display_name || `候选人 #${application.seeker_id}`}</span>
                    <span className={`tag ${statusTag}`}>{statusText}</span>
                  </div>
                  <div className="tiny muted" style={{ marginTop: 6 }}>
                    投递岗位：{application.job_title || `岗位 #${application.job_id}`} {application.job_city ? `· ${application.job_city}` : ''}
                  </div>
                  <div className="tiny muted" style={{ marginTop: 4 }}>
                    投递时间：{formatDateTime(application.created_at)}
                  </div>
                </div>
              </div>
              <div className="ai-tip" style={{ marginTop: 10 }}>
                当前页面只展示数据库中的真实投递记录、简历快照和状态时间线；AI 匹配分、结构化简历画像尚未接入。
              </div>
            </div>

            <div className="cell-group-title">投递简历</div>
            <div className="cell-group">
              <div className="cell" style={{ alignItems: 'flex-start' }}>
                <span style={{ marginRight: 10, fontSize: 22 }}>📄</span>
                <div className="grow" style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 600, wordBreak: 'break-all' }}>{application.resume_file_name || '未记录简历文件名'}</div>
                  {application.resume_snapshot && (
                    <div className="tiny" style={{ marginTop: 6, color: 'var(--wx-text-2)', lineHeight: 1.6 }}>
                      {application.resume_snapshot}
                    </div>
                  )}
                </div>
              </div>
              <div style={{ padding: '0 16px 14px' }}>
                <div className="row gap8">
                  <button className="btn btn-weak btn-sm" disabled={fileLoading} onClick={() => openResumeFile('preview')}>
                    {fileLoading ? '读取中...' : '预览原件'}
                  </button>
                  <button className="btn btn-default btn-sm" disabled={fileLoading} onClick={() => openResumeFile('download')}>
                    下载原件
                  </button>
                </div>
              </div>
            </div>

            {application.cover_message && (
              <>
                <div className="cell-group-title">求职者留言</div>
                <div className="cell-group">
                  <div style={{ padding: '12px 16px', fontSize: 14, lineHeight: 1.7 }}>{application.cover_message}</div>
                </div>
              </>
            )}

            <div className="cell-group-title">解析与匹配状态</div>
            <CellGroup>
              <Cell label="简历结构化解析" value="未接入，P2 开始展示真实字段" />
              <Cell label="AI 匹配分" value="未计算，后续基于简历解析和岗位解析生成" />
              <Cell label="数据来源" value="job_applications / jobs / users / job_application_timelines" />
            </CellGroup>

            <div className="cell-group-title">状态时间线</div>
            <div className="cell-group">
              {timeline.length === 0 && (
                <div className="cell">
                  <span className="grow tiny muted">暂无状态历史</span>
                </div>
              )}
              {timeline.map(item => (
                <div key={item.id} className="cell" style={{ alignItems: 'flex-start' }}>
                  <span style={{ width: 8, height: 8, borderRadius: 999, background: 'var(--wx-green)', margin: '7px 12px 0 2px', flexShrink: 0 }} />
                  <div className="grow">
                    <div style={{ fontWeight: 600, fontSize: 14 }}>
                      {applicationStatusText[item.to_status] || item.to_status}
                    </div>
                    <div className="tiny muted" style={{ marginTop: 3 }}>
                      {formatDateTime(item.created_at)} · {item.actor_role === 'seeker' ? '求职者' : item.actor_role === 'recruiter' ? '招聘者' : '系统'}
                    </div>
                    {item.note && <div className="tiny" style={{ marginTop: 3, color: 'var(--wx-text-2)' }}>{item.note}</div>}
                  </div>
                </div>
              ))}
            </div>

            {application.reject_reason && (
              <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>
                拒绝原因：{application.reject_reason}
              </div>
            )}

            <div className="cell-group-title">Communication status</div>
            <CellGroup>
              <Cell label="Conversation" value={conversationLoading ? 'Loading...' : conversation ? 'Started' : 'Not started'} />
              <Cell label="Contact exchange" value={conversationLoading ? 'Loading...' : exchangeText} />
            </CellGroup>
            {conversation && (
              <div className="btn-block-wrap">
                <button className="btn btn-weak" onClick={() => navigate('/recruiter/chat/' + conversation.id)}>Open conversation</button>
              </div>
            )}

            <div className="btn-block-wrap row gap8" style={{ flexWrap: 'wrap' }}>
              {[
                ['viewed', '标记已查看'],
                ['interview_invited', '邀约面试'],
                ['rejected', '拒绝'],
                ['hired', '录用'],
              ].map(([status, label]) => (
                <button
                  key={status}
                  className={`btn btn-sm ${application.status === status ? 'btn-disabled' : status === 'interview_invited' ? 'btn-primary' : 'btn-default'}`}
                  disabled={updating || application.status === status}
                  onClick={() => changeStatus(status)}
                >
                  {updating ? '处理中...' : label}
                </button>
              ))}
            </div>

            <div className="btn-block-wrap">
              <button className="btn btn-default" onClick={() => navigate('/recruiter/talent')}>返回人才池</button>
            </div>
          </>
        )}
      </div>
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
  const { tagOptions, tagOptionsLoading } = usePublicTagOptions()
  if (!t) return <><NavBar title="人才详情" /><div className="empty" style={{ paddingTop: 100 }}>人才信息不存在</div></>

  const statusLabel = { viewed: '已浏览', chatted: '已沟通', applied: '已投递' }
  const statusColor2 = { viewed: 'tag-gray', chatted: 'tag-green', applied: 'tag-blue' }
  const resume = getTalentResume(t, tagOptions)
  const originalResume = resume?.original
  const talentTagNames = pickPublicTagNames(tagOptions, t.id, 4)

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
              {talentTagNames.length > 0
                ? talentTagNames.map(tg => <span key={tg} className="tag tag-green" style={{ fontSize: 11 }}>{tg}</span>)
                : <span className="tiny muted">{tagOptionsLoading ? '标签加载中...' : '暂无标签库标签'}</span>}
              <span className="ai-badge soft" style={{ fontSize: 10 }}>AI匹配</span>
            </div>
            <div className="tiny muted" style={{ marginTop: 4 }}>最近活跃：{t.lastActive} · 总浏览 {t.viewed} 次</div>
          </div>
        </div>

        {/* 原始简历 */}
        <div className="cell-group-title">演示简历原件（Mock）</div>
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
                <button className="btn btn-default btn-sm" onClick={() => toast('这是演示简历，不提供真实下载')}>下载</button>
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
        <div className="cell-group-title">演示画像摘要（Mock）</div>
        {resume ? (
          <div className="cell-group">
            <div className="cell" style={{ alignItems: 'flex-start' }}>
              <span style={{ marginRight: 10, fontSize: 20 }}>📄</span>
              <div className="grow">
                <div className="row between">
                  <span style={{ fontWeight: 600 }}>{resume.name}的简历</span>
                  <AIBadge soft>演示数据</AIBadge>
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
        <Sheet title="演示简历预览（Mock）" onClose={() => setShowOriginalResume(false)}>
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
                第 1 / {originalResume.pages} 页 · 原始简历预览演示
              </div>
            </div>
            <div className="row gap8" style={{ marginTop: 12 }}>
              <button className="btn btn-default" onClick={() => toast('这是演示预览，没有真实下一页')}>下一页</button>
              <button className="btn btn-primary" onClick={() => toast('这是演示简历，不提供真实下载')}>下载原件</button>
            </div>
          </div>
        </Sheet>
      )}
      <RecruiterBottomNav />
    </>
  )
}
