import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  NavBar, TabBar, CellGroup, Cell, AIBadge, AIButton, AICard, useToast, Switch,
} from '../components/ui.jsx'
import { aiRecommendSubs, aiMock, pickColor } from '../mock/data.js'
import { createMyJobSubscription, getMyNotificationUnreadCount, listMyApplications, listMyConversations, listMyJobSubscriptions, listPublicJobs, listPublicTagLibraryItems, logout, markNotificationTypeRead, searchJobs, updateMyJobSubscription } from '../services/index.js'
import { useProfile } from '../common/ProfileContext.jsx'
import { getLegacyResumeStatus } from '../utils/resumeStatus.js'

const NOTIFICATION_READ_EVENT = 'seeker-notifications-read'

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

export function SeekerApp() {
  const [searchParams] = useSearchParams()
  const initialTab = ['home', 'subs', 'messages', 'profile'].includes(searchParams.get('tab')) ? searchParams.get('tab') : 'home'
  const [tab, setTab] = useState(initialTab)
  const navigate = useNavigate()
  const [unread, setUnread] = useState(0)
  const [notificationCount, setNotificationCount] = useState(0)

  useEffect(() => {
    const nextTab = searchParams.get('tab')
    if (['home', 'subs', 'messages', 'profile'].includes(nextTab)) {
      setTab(nextTab)
    }
  }, [searchParams])

  useEffect(() => {
    if (tab !== 'subs' || notificationCount <= 0) return undefined
    let alive = true
    markNotificationTypeRead('match')
      .then(data => {
        if (!alive) return
        setNotificationCount(data.unread_count || 0)
        window.dispatchEvent(new CustomEvent(NOTIFICATION_READ_EVENT, { detail: { unread_count: data.unread_count || 0 } }))
      })
      .catch(() => {
        window.setTimeout(refreshNotificationCount, 120)
      })
    return () => { alive = false }
  }, [tab, notificationCount])

  useEffect(() => {
    let alive = true
    listMyConversations({ limit: 100 })
      .then(data => {
        if (!alive) return
        setUnread((data.items || []).length)
      })
      .catch(() => {
        if (alive) setUnread(0)
      })
    return () => { alive = false }
  }, [])

  const refreshNotificationCount = () => {
    let alive = true
    getMyNotificationUnreadCount({ type: 'match' })
      .then(data => {
        if (!alive) return
        setNotificationCount(data.unread_count || 0)
      })
      .catch(() => {
        if (alive) setNotificationCount(0)
      })
    return () => { alive = false }
  }

  useEffect(() => {
    const cleanup = refreshNotificationCount()
    const onRead = (event) => {
      const detail = event.detail || {}
      if (typeof detail.unread_count === 'number') {
        setNotificationCount(detail.unread_count)
      } else if (typeof detail.delta === 'number') {
        setNotificationCount(count => Math.max(0, count - 1))
      }
      window.setTimeout(refreshNotificationCount, 120)
    }
    const onFocus = () => refreshNotificationCount()
    window.addEventListener(NOTIFICATION_READ_EVENT, onRead)
    window.addEventListener('focus', onFocus)
    return () => {
      cleanup?.()
      window.removeEventListener(NOTIFICATION_READ_EVENT, onRead)
      window.removeEventListener('focus', onFocus)
    }
  }, [])

  const tabs = [
    { key: 'home', label: '首页', icon: 'H' },
    { key: 'subs', label: '订阅', icon: 'S', badge: notificationCount || null },
    { key: 'messages', label: '消息', icon: 'M', badge: unread || null },
    { key: 'profile', label: '我的', icon: 'P' },
  ]

  return (
    <>
      {tab === 'home' && <Feed onOpen={(id) => navigate('/seeker/job/' + id)} />}
      {tab === 'subs' && <Subscriptions />}
      {tab === 'messages' && <RealMsgList onOpen={(id) => navigate('/seeker/chat/' + id)} />}
      {tab === 'profile' && <Profile notificationCount={notificationCount} onEdit={() => navigate('/seeker/profile/edit')} />}
      <TabBar tabs={tabs} active={tab} onChange={setTab} />
    </>
  )
}

/* ============ 首页岗位流 ============ */
function Feed({ onOpen }) {
  const [sortBy, setSortBy] = useState('match')
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [publicJobs, setPublicJobs] = useState([])
  const [searchJobsResult, setSearchJobsResult] = useState([])
  const [searchingJobs, setSearchingJobs] = useState(false)
  const [searchMode, setSearchMode] = useState('local')
  const [jobsLoading, setJobsLoading] = useState(true)
  const [jobsError, setJobsError] = useState('')
  const [tagOptions, setTagOptions] = useState([])
  const [selectedTagId, setSelectedTagId] = useState('')

  useEffect(() => {
    setJobsLoading(true)
    listPublicJobs({ limit: 100 })
      .then(data => {
        setPublicJobs((data.items || []).map(mapPublicJobToFeed))
        setJobsError('')
      })
      .catch(error => {
        setPublicJobs([])
        setJobsError(error.message || '公开岗位加载失败')
      })
      .finally(() => setJobsLoading(false))
  }, [])

  useEffect(() => {
    let alive = true
    listPublicTagLibraryItems({ limit: 100 })
      .then(data => {
        if (alive) setTagOptions(Array.isArray(data.items) ? data.items : [])
      })
      .catch(() => {
        if (alive) setTagOptions([])
      })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    const keyword = search.trim()
    if (!keyword) {
      setSearchJobsResult([])
      setSearchingJobs(false)
      setSearchMode('local')
      return undefined
    }
    let alive = true
    const timer = window.setTimeout(() => {
      setSearchingJobs(true)
      searchJobs({ q: keyword, tag_id: selectedTagId || undefined, limit: 50 })
        .then(data => {
          if (!alive) return
          setSearchJobsResult((data.items || []).map(mapPublicJobToFeed))
          setSearchMode('api')
        })
        .catch(() => {
          if (!alive) return
          setSearchJobsResult([])
          setSearchMode('local')
        })
        .finally(() => {
          if (alive) setSearchingJobs(false)
        })
    }, 300)
    return () => {
      alive = false
      window.clearTimeout(timer)
    }
  }, [search, selectedTagId])

  let jobs = search.trim() && searchMode === 'api' ? [...searchJobsResult] : [...publicJobs]
  if (search.trim()) {
    const kw = search.trim().toLowerCase()
    if (searchMode !== 'api') {
      jobs = jobs.filter(j => {
        const tagNames = (j.tagRefs || []).map(tag => tag.name || '').filter(Boolean)
        return j.name.toLowerCase().includes(kw) || j.companyShow.toLowerCase().includes(kw) || tagNames.some(t => t.toLowerCase().includes(kw))
      })
    }
  }
  if (filter === 'highMatch') jobs = jobs.filter(j => j.matchScore >= 80)
  if (filter === 'starred') jobs = jobs.filter(j => j.status === 'starred')
  if (selectedTagId && searchMode !== 'api') {
    jobs = jobs.filter(j => (j.tagRefs || []).some(tag => String(tag.id) === String(selectedTagId)))
  }
  if (sortBy === 'match') jobs.sort((a, b) => b.matchScore - a.matchScore)
  if (sortBy === 'salary') jobs.sort((a, b) => parseInt(b.salary) - parseInt(a.salary))
  if (sortBy === 'time') jobs.reverse()

  return (
    <>
      <NavBar title="发现岗位" back={false} />
      <div className="page has-tabbar">
        <div style={{ background: '#fff', padding: '10px 16px' }}>
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="搜索职位、公司"
            style={{ width: '100%', background: 'var(--wx-surface-2)', borderRadius: 999, padding: '8px 14px', fontSize: 14, border: 'none', outline: 'none', color: 'var(--wx-text)', boxSizing: 'border-box' }} />
        </div>
        {search && (
          <div style={{ background: '#fff', padding: '4px 16px 8px', fontSize: 12, color: 'var(--wx-text-light)' }}>
            {searchingJobs ? `正在搜索“${search}”...` : `搜索“${search}”找到 ${jobs.length} 个岗位`}
            <span style={{ marginLeft: 8 }}>{searchMode === 'api' ? '语义搜索' : '本地筛选'}</span>
          </div>
        )}
        {tagOptions.length > 0 && (
          <div className="row gap6" style={{ background: '#fff', padding: '0 16px 8px', overflowX: 'auto' }}>
            <span
              className={`tag ${selectedTagId === '' ? 'tag-green' : 'tag-gray'}`}
              style={{ cursor: 'pointer', fontSize: 11, flexShrink: 0 }}
              onClick={() => setSelectedTagId('')}
            >
              全部标签
            </span>
            {tagOptions.slice(0, 12).map(item => (
              <span
                key={item.id}
                className={`tag ${String(item.id) === String(selectedTagId) ? 'tag-green' : 'tag-gray'}`}
                style={{ cursor: 'pointer', fontSize: 11, flexShrink: 0 }}
                onClick={() => setSelectedTagId(String(item.id))}
              >
                {item.name}
              </span>
            ))}
          </div>
        )}

        <div className="row between padx" style={{ background: '#fff', padding: '6px 16px', borderTop: '0.5px solid var(--wx-line-light)' }}>
          <div className="row gap6">
            {[{ k: 'all', l: '全部' }, { k: 'highMatch', l: '匹配80%+' }, { k: 'starred', l: '收藏' }].map(f => (
              <span key={f.k} className={`tag ${filter === f.k ? 'tag-green' : 'tag-gray'}`}
                style={{ cursor: 'pointer', fontSize: 11 }} onClick={() => setFilter(f.k)}>{f.l}</span>
            ))}
          </div>
        </div>
        <div className="row between padx" style={{ background: '#fff', padding: '4px 16px 8px' }}>
          <div className="row gap6" style={{ color: 'var(--wx-green-dark)', fontSize: 11 }}>
            <AIBadge soft>AI排序</AIBadge>
            {[{ k: 'match', l: '匹配度' }, { k: 'time', l: '最新' }, { k: 'salary', l: '薪资' }].map(s => (
              <span key={s.k} style={{ cursor: 'pointer', fontWeight: sortBy === s.k ? 600 : 400,
                color: sortBy === s.k ? 'var(--wx-green-dark)' : 'var(--wx-text-light)' }}
                onClick={() => setSortBy(s.k)}>{s.l}</span>
            ))}
          </div>
          <span className="tiny muted" style={{ fontSize: 11 }}>已加载 {jobs.length} 个岗位</span>
        </div>

        {jobsLoading && <div className="ai-tip" style={{ margin: 16 }}>正在加载岗位...</div>}
        {jobsError && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{jobsError}</div>}
        {!jobsLoading && !jobsError && jobs.map(j => (
          <div key={j.id} className="job-card" onClick={() => onOpen(j.id)} style={{ position: 'relative' }}>
            <div className="jc-top">
              <span className="jc-name">{j.name}</span>
              <span className="jc-salary">{j.salary}</span>
            </div>
            <div className="jc-meta">
              <span className="tag tag-gray">{j.city}</span>
              <span className="tag tag-gray">{j.exp}</span>
              <span className="tag tag-gray">{j.edu}</span>
              <span className="tag tag-green">匹配 {j.matchScore}%</span>
            </div>
            <div className="row gap6" style={{ background: 'var(--ai-bg)', borderRadius: 6, padding: '6px 10px', margin: '6px 0' }}>
              <AIBadge>AI亮点</AIBadge>
              <span className="tiny" style={{ color: '#3a5a48' }}>{j.aiHighlight}</span>
            </div>
            <div className="jc-company">
              <span className="jc-logo">{j.companyShow[0]}</span>
              <span>{j.companyShow}</span>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
function mapPublicJobToFeed(job) {
  const salary = `${job.salary_min}K-${job.salary_max}K`
  return {
    id: job.id,
    name: job.title,
    salary,
    city: job.city,
    exp: job.experience,
    edu: job.education,
    tagRefs: job.tag_refs || [],
    companyShow: job.recruiter_display_name || '认证企业',
    matchScore: Math.max(60, Math.round(job.score || 80)),
    aiHighlight: job.reason || '岗位已通过平台审核，当前对求职者可见。',
    status: 'new',
  }
}

function parseSubscriptionText(text) {
  const raw = text.trim()
  const knownCities = ['北京', '上海', '深圳', '广州', '杭州', '南京', '成都', '武汉', '西安', '苏州']
  const city = knownCities.find(c => raw.includes(c)) || ''
  const salaryMatch = raw.match(/(\d+)\s*[kK万]/)
  const salary_min = salaryMatch ? Number(salaryMatch[1]) : undefined
  const stopWords = new Set(['我', '想', '找', '一个', '一份', '工作', '岗位', '职位', '月薪', '薪资', '以上', '左右', '的', '和', '或'])
  const keywords = raw
    .replace(/[，。,.、/|+]/g, ' ')
    .split(/\s+/)
    .map(s => s.trim())
    .filter(Boolean)
    .filter(s => !knownCities.includes(s) && !stopWords.has(s) && !/^\d+[kK万]?$/.test(s))
    .slice(0, 5)
  return {
    name: keywords.slice(0, 2).join(' / ') || raw.slice(0, 20),
    keywords: keywords.length ? keywords : [raw.slice(0, 20)],
    city: city || undefined,
    salary_min,
    active: true,
  }
}

function formatSubscriptionSalary(sub) {
  if (sub.salary_min && sub.salary_max) return `${sub.salary_min}K-${sub.salary_max}K`
  if (sub.salary_min) return `${sub.salary_min}K+`
  if (sub.salary_max) return `${sub.salary_max}K以内`
  return '薪资不限'
}

function Subscriptions() {
  const toast = useToast()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [subs, setSubs] = useState([])
  const [nl, setNl] = useState('')
  const [loading, setLoading] = useState(true)
  const [parsing, setParsing] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [error, setError] = useState('')

  const loadSubscriptions = () => {
    setLoading(true)
    listMyJobSubscriptions({ limit: 100 })
      .then(data => {
        const items = data.items || []
        const targetId = Number(searchParams.get('subscriptionId'))
        setSubs(items)
        if (targetId && items.some(item => item.id === targetId)) {
          setExpandedId(targetId)
        }
        setError('')
      })
      .catch(err => {
        setSubs([])
        setError(err.message || '订阅加载失败')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadSubscriptions()
  }, [searchParams])

  const createSubscription = async (payload) => {
    const created = await createMyJobSubscription(payload)
    setSubs(arr => [created, ...arr.filter(item => item.id !== created.id)])
    setExpandedId(created.id)
    return created
  }

  const parseNL = async () => {
    if (!nl.trim()) { toast('请先输入求职意向'); return }
    setParsing(true)
    try {
      const created = await createSubscription(parseSubscriptionText(nl))
      setNl('')
      toast(`已创建订阅，匹配到 ${created.match_count || 0} 个岗位`, '✓')
    } catch (err) {
      toast(err.message || '创建订阅失败')
    } finally {
      setParsing(false)
    }
  }

  const adoptRecommendation = async (recommendation) => {
    try {
      const created = await createSubscription({
        name: recommendation.keywords.join(' / '),
        keywords: recommendation.keywords,
        city: recommendation.city,
        salary_min: Number(String(recommendation.salary || '').match(/\d+/)?.[0]) || undefined,
        active: true,
      })
      toast(`已采纳，匹配到 ${created.match_count || 0} 个岗位`)
    } catch (err) {
      toast(err.message || '采纳失败')
    }
  }

  const toggleSubscription = async (event, sub) => {
    event.stopPropagation()
    try {
      const updated = await updateMyJobSubscription(sub.id, { active: !sub.active })
      setSubs(arr => arr.map(item => item.id === sub.id ? updated : item))
    } catch (err) {
      toast(err.message || '更新订阅失败')
    }
  }

  return (
    <>
      <NavBar title="订阅画像" back={false} />
      <div className="page has-tabbar">
        <div className="cell-group" style={{ marginTop: 10 }}>
          <div style={{ padding: 16 }}>
            <div className="row gap6" style={{ marginBottom: 8 }}><AIBadge soft>AI解析</AIBadge><span className="tiny muted">一句话描述求职意向，自动生成订阅</span></div>
            <div className="row gap8">
              <input className="grow" value={nl} placeholder="如：上海 React 前端 20K+"
                onChange={e => setNl(e.target.value)}
                style={{ background: 'var(--wx-surface-2)', borderRadius: 8, padding: '9px 12px', fontSize: 14 }} />
              <AIButton onClick={parseNL} loading={parsing}>{parsing ? '创建中' : '创建'}</AIButton>
            </div>
          </div>
        </div>

        <div className="cell-group-title">AI 为你推荐</div>
        <div className="cell-group">
          {aiRecommendSubs.map((r, i) => (
            <div key={i} className="cell">
              <div className="grow">
                <div>{r.keywords.join(' / ')}</div>
                <div className="tiny muted" style={{ marginTop: 2 }}>{r.city} / {r.salary}</div>
              </div>
              <button className="btn btn-weak btn-sm" onClick={() => adoptRecommendation(r)}>采纳</button>
            </div>
          ))}
        </div>

        <div className="cell-group-title">我的订阅画像（{subs.length}/10）</div>
        <div className="cell-group">
          {loading && <div className="cell"><span className="grow tiny muted">正在加载订阅...</span></div>}
          {error && <div className="cell"><span className="grow tiny" style={{ color: 'var(--wx-red)' }}>{error}</span></div>}
          {!loading && !error && subs.length === 0 && <div className="cell"><span className="grow tiny muted">暂无订阅，创建一个后会自动匹配岗位</span></div>}
          {!loading && !error && subs.map(s => {
            const matched = s.matched_jobs || []
            const isExpanded = expandedId === s.id
            return (
              <div key={s.id}>
                <div className="cell" style={{ cursor: 'pointer' }} onClick={() => setExpandedId(isExpanded ? null : s.id)}>
                  <div className="grow">
                    <div>{(s.keywords || []).join(' / ')}</div>
                    <div className="tiny muted" style={{ marginTop: 2 }}>{s.city || '城市不限'} / {formatSubscriptionSalary(s)} / 匹配 {s.match_count || 0} 个岗位</div>
                  </div>
                  <span style={{ marginRight: 8, fontSize: 12, color: 'var(--wx-text-light)' }}>{isExpanded ? '收起' : '展开'}</span>
                  <Switch on={s.active} onClick={(e) => toggleSubscription(e, s)} />
                </div>
                {isExpanded && (
                  <div style={{ background: 'var(--wx-surface-2)', padding: '8px 16px 12px' }}>
                    {matched.length === 0 ? (
                      <div className="tiny muted" style={{ padding: '8px 0', textAlign: 'center' }}>暂无匹配岗位，试试调整关键词</div>
                    ) : (
                      matched.map(j => (
                        <div key={j.id} className="row between" style={{ padding: '8px 0', borderBottom: '0.5px solid var(--wx-line-light)', cursor: 'pointer', fontSize: 13 }}
                          onClick={() => navigate('/seeker/job/' + j.id)}>
                          <span style={{ fontWeight: 500 }}>{j.title}</span>
                          <span className="tag tag-green" style={{ fontSize: 11 }}>{j.city}</span>
                          <span className="cell-arrow">›</span>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </>
  )
}

/* ============ 求职者消息列表（旧 mock 入口保留） ============ */
function MsgList() {
  return (
    <>
      <NavBar title="消息" back={false} />
      <div className="page has-tabbar" style={{ background: '#fff' }}>
        <div className="ai-tip" style={{ margin: 16 }}>消息列表已接入真实会话。</div>
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
        {!loading && items.map(c => (
          <div key={c.id} className="cell link" onClick={() => onOpen(c.id)} style={{ alignItems: 'flex-start', padding: '12px 16px' }}>
            <span className="avatar" style={{ width: 46, height: 46, borderRadius: 6, background: pickColor(c.recruiter_id || 0), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 17, fontWeight: 600, marginRight: 12, flexShrink: 0 }}>{(c.recruiter_display_name || '招')[0]}</span>
            <div className="grow" style={{ overflow: 'hidden' }}>
              <div className="row between"><span style={{ fontWeight: 500 }}>{c.recruiter_display_name || '招聘方'}</span><span className="tiny muted">{c.last_message_at ? new Date(c.last_message_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''}</span></div>
              <div className="tiny muted" style={{ marginTop: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                <LeadStatusTag item={c} />
                {c.latest_message?.content || '暂无消息'}
              </div>
              <div className="tiny" style={{ color: 'var(--wx-text-light)', marginTop: 3 }}>{c.job_title || `岗位 #${c.job_id}`}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

/* ============ 求职者个人中心 ============ */
function Profile({ notificationCount = 0, onEdit }) {
  const navigate = useNavigate()
  const { completed, hasResume, resume, profile } = useProfile()
  const resumeStatus = getLegacyResumeStatus(resume)
  const [applicationCount, setApplicationCount] = useState(null)

  useEffect(() => {
    let alive = true
    listMyApplications({ limit: 1 })
      .then(data => {
        if (!alive) return
        setApplicationCount(data.total ?? (data.items || []).length)
      })
      .catch(() => {
        if (alive) setApplicationCount(null)
      })
    return () => { alive = false }
  }, [])

  const profileFields = [
    profile?.real_name,
    profile?.gender,
    profile?.education,
    profile?.experience_years !== null && profile?.experience_years !== undefined ? String(profile.experience_years) : '',
    profile?.target_position,
    profile?.expected_salary,
    profile?.city,
  ]
  const filled = profileFields.filter(Boolean).length + (hasResume ? 1 : 0)
  const pct = Math.round((filled / 8) * 100)
  const displayName = profile?.real_name || '未填写姓名'
  const avatarText = (profile?.real_name || '我').slice(0, 1)
  const summary = [
    profile?.target_position || '未填写期望岗位',
    profile?.experience_years !== null && profile?.experience_years !== undefined ? `${profile.experience_years}年经验` : '未填写经验',
    profile?.education || '未填写学历',
  ].join(' / ')

  return (
    <>
      <NavBar title="我的" back={false} />
      <div className="page has-tabbar">
        <div className="row" style={{ background: '#fff', padding: '20px 16px', gap: 14 }}>
          <span style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--wx-green-bg)', color: 'var(--wx-green-dark)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, fontWeight: 700 }}>{avatarText}</span>
          <div className="grow">
            <div style={{ fontSize: 17, fontWeight: 600 }}>{displayName} {!completed && <span className="tag tag-gray" style={{ marginLeft: 4 }}>待完善</span>}</div>
            <div className="tiny muted" style={{ marginTop: 4 }}>{summary}</div>
          </div>
        </div>

        <div style={{ background: '#fff', padding: '0 16px 16px' }}>
          <div className="row between tiny" style={{ marginBottom: 6 }}><span className="muted">信息完整度</span><span style={{ color: 'var(--wx-green)', fontWeight: 600 }}>{pct}%</span></div>
          <div className="progress"><div className="bar" style={{ width: pct + '%' }} /></div>
          <div className="row gap6" style={{ marginTop: 8 }}><AIBadge soft>AI提示</AIBadge><span className="tiny muted">完善能力信息可提升招聘者关注度</span></div>
        </div>

        <CellGroup>
          <Cell icon="N" iconBg="#FFE6E6" label="通知中心" value={notificationCount ? `${notificationCount} 条新提醒` : ''} link onClick={() => navigate('/seeker/notifications')} />
          <Cell icon="E" iconBg="#ECF9F1" label="编辑个人信息" link onClick={onEdit} />
          <Cell icon="R" iconBg="#E8F5FF" label="上传简历" value={resumeStatus.label} link onClick={() => navigate('/seeker/resume')} />
          <Cell icon="P" iconBg="#ECF9F1" label="我的简历画像" link onClick={() => navigate('/seeker/portrait')} />
          <Cell icon="A" iconBg="#E8F5FF" label="投递记录" value={applicationCount === null ? '读取中' : `${applicationCount} 条`} link onClick={() => navigate('/seeker/applications')} />
          <Cell icon="S" iconBg="#FFF3E6" label="我的订阅" link onClick={() => navigate('/seeker/home?tab=subs')} />
          <Cell icon="H" iconBg="#F0F0F0" label="浏览记录" link onClick={() => navigate('/seeker/history')} />
          <Cell icon="F" iconBg="#FFF7E6" label="我的收藏" link onClick={() => navigate('/seeker/favorites')} />
        </CellGroup>
        <CellGroup>
          <Cell icon="C" iconBg="#ECF9F1" label="智能客服" link onClick={() => navigate('/support')} />
          <Cell icon="P" iconBg="#E8F5FF" label="隐私设置" link />
          <Cell icon="A" iconBg="#F2F2F2" label="账号设置" link />
        </CellGroup>
        <div className="btn-block-wrap"><button className="btn btn-default" onClick={logout}>退出登录</button></div>
      </div>
    </>
  )
}
/* ============ 求职者注册 ============ */
export function SeekerRegister() {
  const navigate = useNavigate()
  const toast = useToast()
  const [mode, setMode] = useState('')
  const [names, setNames] = useState([])
  const [picked, setPicked] = useState('')

  const genNames = () => {
    setNames(aiMock.virtualNames || ['清风求职者', '星河候选人', '松木同学'])
  }

  const submit = () => {
    if (!mode || (mode === 'virtual' && !picked)) return
    toast('注册完成', '✓')
    setTimeout(() => navigate('/seeker/home'), 500)
  }

  return (
    <>
      <NavBar title="注册" onBack={() => navigate('/')} />
      <div className="page" style={{ paddingBottom: 90 }}>
        <div className="pad center" style={{ background: '#fff' }}>
          <div style={{ fontWeight: 600, fontSize: 17 }}>微信授权快速注册</div>
          <div className="tiny muted" style={{ marginTop: 4 }}>选择求职者展示身份</div>
        </div>

        <div className="cell-group-title">选择展示身份</div>
        <div className="pad" style={{ background: '#fff' }}>
          <div className="row gap12">
            <div className={`opt-card grow center ${mode === 'real' ? 'sel' : ''}`} onClick={() => setMode('real')}>
              <div style={{ marginTop: 4 }}>实名</div>
              <div className="tiny muted">使用真实姓名</div>
            </div>
            <div className={`opt-card grow center ${mode === 'virtual' ? 'sel' : ''}`} onClick={() => { setMode('virtual'); genNames() }}>
              <div style={{ marginTop: 4 }}>虚拟名</div>
              <div className="tiny muted">保护隐私</div>
            </div>
          </div>
        </div>

        {mode === 'virtual' && (
          <>
            <div className="cell-group-title row between" style={{ paddingRight: 16 }}>
              <span>AI 生成的虚拟名</span>
              <span className="tiny" style={{ color: 'var(--wx-green-dark)' }} onClick={genNames}>换一批</span>
            </div>
            <div className="pad" style={{ background: '#fff' }}>
              <div className="row gap12">
                {names.map(n => (
                  <div key={n} className={`opt-card grow center ${picked === n ? 'sel' : ''}`} onClick={() => setPicked(n)} style={{ padding: '14px 8px' }}>
                    <div style={{ fontSize: 17, fontWeight: 600 }}>{n}</div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
      <div className="page-foot"><button className={`btn ${mode && (mode === 'real' || picked) ? 'btn-primary' : 'btn-disabled'}`} onClick={submit}>完成注册</button></div>
    </>
  )
}
