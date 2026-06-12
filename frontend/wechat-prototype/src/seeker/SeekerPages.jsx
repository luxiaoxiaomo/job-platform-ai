import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  NavBar, TabBar, CellGroup, Cell, AIBadge, AIButton, AICard, useToast, Switch,
} from '../components/ui.jsx'
import { feedJobs, seekerChats, initialSubs, aiRecommendSubs, aiMock, pickColor } from '../mock/data.js'

/* ============ 应聘者 Tab 容器 ============ */
export function SeekerApp() {
  const [tab, setTab] = useState('home')
  const navigate = useNavigate()
  const unread = seekerChats.reduce((s, c) => s + c.unread, 0)
  const tabs = [
    { key: 'home', label: '首页', icon: '🏠' },
    { key: 'subs', label: '订阅', icon: '🔔' },
    { key: 'messages', label: '消息', icon: '💬', badge: unread || null },
    { key: 'profile', label: '我的', icon: '👤' },
  ]
  return (
    <>
      {tab === 'home' && <Feed onOpen={(id) => navigate('/seeker/job/' + id)} />}
      {tab === 'subs' && <Subscriptions />}
      {tab === 'messages' && <MsgList onOpen={(id) => navigate('/seeker/chat/' + id)} />}
      {tab === 'profile' && <Profile onEdit={() => navigate('/seeker/profile/edit')} />}
      <TabBar tabs={tabs} active={tab} onChange={setTab} />
    </>
  )
}

/* ============ 首页岗位流（AI 亮点 + 排序/筛选 + 状态 + 统计） ============ */
function Feed({ onOpen }) {
  const [sortBy, setSortBy] = useState('match') // match | time | salary
  const [filter, setFilter] = useState('all') // all | highMatch | unread | starred
  const [search, setSearch] = useState('')
  const statusIcon = { new: '🆕', viewed: '👁', chatted: '💬', archived: '🗑', starred: '⭐' }

  let jobs = [...feedJobs]
  if (search.trim()) {
    const kw = search.trim().toLowerCase()
    jobs = jobs.filter(j => j.name.toLowerCase().includes(kw) || j.companyShow.toLowerCase().includes(kw) || j.tags.some(t => t.toLowerCase().includes(kw)))
  }
  if (filter === 'highMatch') jobs = jobs.filter(j => j.matchScore >= 80)
  if (filter === 'starred') jobs = jobs.filter(j => j.status === 'starred')
  if (sortBy === 'match') jobs.sort((a, b) => b.matchScore - a.matchScore)
  if (sortBy === 'salary') jobs.sort((a, b) => parseInt(b.salary) - parseInt(a.salary))
  if (sortBy === 'time') jobs.reverse()

  return (
    <>
      <NavBar title="发现岗位" back={false} />
      <div className="page has-tabbar">
        <div style={{ background: '#fff', padding: '10px 16px' }}>
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="🔍 搜索职位、公司"
            style={{ width: '100%', background: 'var(--wx-surface-2)', borderRadius: 999, padding: '8px 14px', fontSize: 14, border: 'none', outline: 'none', color: 'var(--wx-text)', boxSizing: 'border-box' }} />
        </div>
        {search && (
          <div style={{ background: '#fff', padding: '4px 16px 8px', fontSize: 12, color: 'var(--wx-text-light)' }}>
            搜索「{search}」找到 {jobs.length} 个岗位
          </div>
        )}

        {/* A4: 推送统计 + A6: 排序/筛选 */}
        <div className="row between padx" style={{ background: '#fff', padding: '6px 16px', borderTop: '0.5px solid var(--wx-line-light)' }}>
          <div className="row gap6">
            {[{ k: 'all', l: '全部' }, { k: 'highMatch', l: '匹配≥80%' }, { k: 'starred', l: '⭐收藏' }].map(f => (
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
          <span className="tiny muted" style={{ fontSize: 11 }}>⚡ AI 累计推送 {feedJobs.length} 个岗位</span>
        </div>

        {jobs.map(j => (
          <div key={j.id} className="job-card" onClick={() => onOpen(j.id)} style={{ position: 'relative' }}>
            {/* A5: 状态标识 */}
            {j.status && j.status !== 'new' && (
              <span style={{ position: 'absolute', top: 8, right: 12, fontSize: 13, opacity: .7 }} title={j.status}>
                {statusIcon[j.status]}
              </span>
            )}
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

/* ============ 关键词订阅（AI 推荐 + 自然语言解析） ============ */
function Subscriptions() {
  const toast = useToast()
  const navigate = useNavigate()
  const [subs, setSubs] = useState(initialSubs)
  const [nl, setNl] = useState('')
  const [parsing, setParsing] = useState(false)
  const [expandedId, setExpandedId] = useState(null)

  // 匹配某订阅画像的岗位
  const matchJobs = (sub) => feedJobs.filter(j =>
    sub.keywords.some(kw => j.name.includes(kw) || j.tags.some(t => t.includes(kw)))
  )

  const parseNL = () => {
    if (!nl.trim()) { toast('请先输入求职意向'); return }
    setParsing(true)
    setTimeout(() => {
      setParsing(false)
      setSubs(s => [{ id: Date.now(), keywords: ['设计师', 'UI'], city: '上海', salary: '10K+', active: true }, ...s])
      setNl('')
      toast('已解析并创建订阅', '✓')
    }, 1300)
  }

  return (
    <>
      <NavBar title="订阅画像" back={false} />
      <div className="page has-tabbar">
        {/* 自然语言解析 */}
        <div className="cell-group" style={{ marginTop: 10 }}>
          <div style={{ padding: 16 }}>
            <div className="row gap6" style={{ marginBottom: 8 }}><AIBadge soft>AI解析</AIBadge><span className="tiny muted">一句话描述求职意向，自动生成订阅</span></div>
            <div className="row gap8">
              <input className="grow" value={nl} placeholder="如：上海月薪过万的设计工作"
                onChange={e => setNl(e.target.value)}
                style={{ background: 'var(--wx-surface-2)', borderRadius: 8, padding: '9px 12px', fontSize: 14 }} />
              <AIButton onClick={parseNL} loading={parsing}>{parsing ? '解析中' : '解析'}</AIButton>
            </div>
          </div>
        </div>

        {/* AI 推荐订阅 */}
        <div className="cell-group-title">⚡ AI 为你推荐</div>
        <div className="cell-group">
          {aiRecommendSubs.map((r, i) => (
            <div key={i} className="cell">
              <div className="grow">
                <div>{r.keywords.join(' · ')}</div>
                <div className="tiny muted" style={{ marginTop: 2 }}>{r.city} · {r.salary}</div>
              </div>
              <button className="btn btn-weak btn-sm" onClick={() => { setSubs(s => [{ id: Date.now(), keywords: r.keywords, city: r.city, salary: r.salary, active: true }, ...s]); toast('已采纳推荐订阅') }}>采纳</button>
            </div>
          ))}
        </div>

        {/* 我的订阅 */}
        <div className="cell-group-title">我的订阅画像（{subs.length}/10）</div>
        <div className="cell-group">
          {subs.map(s => {
            const matched = matchJobs(s)
            const isExpanded = expandedId === s.id
            return (
              <div key={s.id}>
                <div className="cell" style={{ cursor: 'pointer' }} onClick={() => setExpandedId(isExpanded ? null : s.id)}>
                  <div className="grow">
                    <div>{s.keywords.join(' · ')}</div>
                    <div className="tiny muted" style={{ marginTop: 2 }}>{s.city} · {s.salary} · 匹配 {matched.length} 个岗位</div>
                  </div>
                  <span style={{ marginRight: 8, fontSize: 12, color: 'var(--wx-text-light)' }}>{isExpanded ? '收起 ▲' : '展开 ▼'}</span>
                  <Switch on={s.active} onClick={(e) => { e.stopPropagation(); setSubs(arr => arr.map(x => x.id === s.id ? { ...x, active: !x.active } : x)) }} />
                </div>
                {isExpanded && (
                  <div style={{ background: 'var(--wx-surface-2)', padding: '8px 16px 12px' }}>
                    {matched.length === 0 ? (
                      <div className="tiny muted" style={{ padding: '8px 0', textAlign: 'center' }}>暂无匹配岗位，试试调整关键词</div>
                    ) : (
                      matched.map(j => (
                        <div key={j.id} className="row between" style={{ padding: '8px 0', borderBottom: '0.5px solid var(--wx-line-light)', cursor: 'pointer', fontSize: 13 }}
                          onClick={() => navigate('/seeker/job/' + j.id)}>
                          <span style={{ fontWeight: 500 }}>{j.name}</span>
                          <span className="tag tag-green" style={{ fontSize: 11 }}>匹配 {j.matchScore}%</span>
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

/* ============ 应聘者消息列表 ============ */
function MsgList({ onOpen }) {
  return (
    <>
      <NavBar title="消息" back={false} />
      <div className="page has-tabbar" style={{ background: '#fff' }}>
        {seekerChats.map(c => (
          <div key={c.id} className="cell link" onClick={() => onOpen(c.id)} style={{ alignItems: 'flex-start', padding: '12px 16px' }}>
            <span className="avatar" style={{ width: 46, height: 46, borderRadius: 6, background: pickColor(c.logoIdx), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 17, fontWeight: 600, marginRight: 12, flexShrink: 0 }}>{c.name[0]}</span>
            <div className="grow" style={{ overflow: 'hidden' }}>
              <div className="row between"><span style={{ fontWeight: 500 }}>{c.name}</span><span className="tiny muted">{c.time}</span></div>
              <div className="tiny muted" style={{ marginTop: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {c.isInterview && <span className="tag tag-orange" style={{ marginRight: 4 }}>面试邀约</span>}{c.preview}
              </div>
              <div className="tiny" style={{ color: 'var(--wx-text-light)', marginTop: 3 }}>{c.job}</div>
            </div>
            {c.unread > 0 && <span className="tab-badge" style={{ position: 'static', marginLeft: 8 }}>{c.unread}</span>}
          </div>
        ))}
      </div>
    </>
  )
}

/* ============ 应聘者个人中心（信息完整度） ============ */
function Profile({ onEdit }) {
  const navigate = useNavigate()
  const pct = 65
  return (
    <>
      <NavBar title="我的" back={false} />
      <div className="page has-tabbar">
        <div className="row" style={{ background: '#fff', padding: '20px 16px', gap: 14 }}>
          <span style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--wx-green-bg)', color: 'var(--wx-green-dark)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, fontWeight: 700 }}>李</span>
          <div className="grow">
            <div style={{ fontSize: 17, fontWeight: 600 }}>李然 <span className="tag tag-gray" style={{ marginLeft: 4 }}>虚拟名</span></div>
            <div className="tiny muted" style={{ marginTop: 4 }}>前端开发 · 5年经验 · 本科</div>
          </div>
        </div>

        <div style={{ background: '#fff', padding: '0 16px 16px' }}>
          <div className="row between tiny" style={{ marginBottom: 6 }}><span className="muted">信息完整度</span><span style={{ color: 'var(--wx-green)', fontWeight: 600 }}>{pct}%</span></div>
          <div className="progress"><div className="bar" style={{ width: pct + '%' }} /></div>
          <div className="row gap6" style={{ marginTop: 8 }}>
            <AIBadge soft>AI提示</AIBadge><span className="tiny muted">完善「能力信息」可提升招聘者关注度</span>
          </div>
        </div>

        <CellGroup>
          <Cell icon="🔔" iconBg="#FFE6E6" label="通知中心" value="2 条未读" link onClick={() => navigate('/seeker/notifications')} />
          <Cell icon="📝" iconBg="#ECF9F1" label="编辑个人信息" link onClick={onEdit} />
          <Cell icon="📄" iconBg="#E8F5FF" label="上传简历" value="AI 解析" link onClick={() => navigate('/seeker/resume')} />
          <Cell icon="🎯" iconBg="#ECF9F1" label="我的简历画像" value="中高级前端" link onClick={() => navigate('/seeker/portrait')} />
          <Cell icon="📨" iconBg="#E8F5FF" label="投递记录" value="3 条" link onClick={() => navigate('/seeker/applications')} />
          <Cell icon="🔔" iconBg="#FFF3E6" label="我的订阅" value="3 组" link />
          <Cell icon="🕐" iconBg="#F0F0F0" label="浏览记录" value="6 条" link onClick={() => navigate('/seeker/history')} />
          <Cell icon="⭐" iconBg="#FFF7E6" label="我的收藏" value="3 个职位" link onClick={() => navigate('/seeker/favorites')} />
          <Cell icon="📝" iconBg="#FFF0E6" label="申请测评" value="即将上线" link onClick={() => navigate('/support')} />
          <Cell icon="📚" iconBg="#F0E6FF" label="参加学习" value="即将上线" link onClick={() => navigate('/support')} />
        </CellGroup>
        <CellGroup>
          <Cell icon="💬" iconBg="#ECF9F1" label="智能客服" link onClick={() => navigate('/support')} />
          <Cell icon="🛡" iconBg="#E8F5FF" label="隐私设置" link />
          <Cell icon="⚙️" iconBg="#F2F2F2" label="账号设置" link />
        </CellGroup>
      </div>
    </>
  )
}

/* ============ 应聘者注册（AI 虚拟名） ============ */
export function SeekerRegister() {
  const navigate = useNavigate()
  const toast = useToast()
  const [mode, setMode] = useState('') // real | virtual
  const [names, setNames] = useState([])
  const [picked, setPicked] = useState('')

  const genNames = () => {
    setNames(aiMock.virtualNames)
  }

  return (
    <>
      <NavBar title="注册" onBack={() => navigate('/')} />
      <div className="page" style={{ paddingBottom: 90 }}>
        <div className="pad center" style={{ background: '#fff' }}>
          <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--wx-green-bg)', margin: '12px auto', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 30 }}>💼</div>
          <div style={{ fontWeight: 600, fontSize: 17 }}>微信授权快速注册</div>
          <div className="tiny muted" style={{ marginTop: 4 }}>无需下载 App，授权即用</div>
        </div>

        <div className="cell-group-title">选择展示身份</div>
        <div className="pad" style={{ background: '#fff' }}>
          <div className="row gap12">
            <div className={`opt-card grow center ${mode === 'real' ? 'sel' : ''}`} onClick={() => setMode('real')}>
              <div style={{ fontSize: 22 }}>🙂</div><div style={{ marginTop: 4 }}>实名</div>
              <div className="tiny muted">使用真实姓名</div>
            </div>
            <div className={`opt-card grow center ${mode === 'virtual' ? 'sel' : ''}`} onClick={() => { setMode('virtual'); genNames() }}>
              <div style={{ fontSize: 22 }}>🎭</div><div style={{ marginTop: 4 }}>虚拟名</div>
              <div className="tiny muted">保护隐私</div>
            </div>
          </div>
        </div>

        {mode === 'virtual' && (
          <>
            <div className="cell-group-title row between" style={{ paddingRight: 16 }}>
              <span>⚡ AI 生成的虚拟名</span>
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
              <div className="ai-tip" style={{ marginTop: 10 }}>⚡ AI 生成，保持真实感、中性化，2-3 个汉字</div>
            </div>
          </>
        )}
      </div>
      <div className="page-foot">
        <button className={`btn ${mode && (mode === 'real' || picked) ? 'btn-primary' : 'btn-disabled'}`}
          onClick={() => { if (!mode || (mode === 'virtual' && !picked)) return; toast('注册成功', '🎉'); setTimeout(() => navigate('/seeker/home'), 800) }}>
          完成注册
        </button>
      </div>
    </>
  )
}
