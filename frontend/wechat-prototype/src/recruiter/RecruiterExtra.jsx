import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, AIBadge, AICard, useToast } from '../components/ui.jsx'
import { RecruiterBottomNav } from './RecruiterBottomNav.jsx'
import { RadarChart, LineChart, ScoreBar } from '../components/charts.jsx'
import { candidateMatch, candidateCompare, candidateList, statTrend, aggregateStats, myJobs, pickColor } from '../mock/data.js'
import { ShareSheet } from '../seeker/SeekerExtra.jsx'
import { getContactExchangeStats, getRecruiterApplicationStats, getRecruiterBusinessLoopStats, getRecruiterDeepDiveStats, listMyJobs } from '../services/index.js'
import { pickPublicTagNames, usePublicTagOptions } from '../common/usePublicTagOptions.js'

/* ============ 候选人分析（列表 + 单人选匹配 + 对比） ============ */
export function RecruiterCandidate() {
  const navigate = useNavigate()
  const toast = useToast()
  const [tab, setTab] = useState('list') // list | match | compare
  const [selectedId, setSelectedId] = useState(null)
  const [showShare, setShowShare] = useState(false)
  const c = candidateMatch
  const { tagOptions, tagOptionsLoading } = usePublicTagOptions()
  const candidateTagNames = (candidate, count = 3) => pickPublicTagNames(tagOptions, candidate?.id || 0, count)

  return (
    <>
      <NavBar title="候选人分析" right={<span onClick={() => setShowShare(true)}>推荐</span>} />
      {showShare && <ShareSheet title="推荐该候选人给其他招聘者" onClose={() => setShowShare(false)} />}
      <div className="page" style={{ paddingBottom: 80 }}>

        {/* tab 切换 */}
        <div className="row" style={{ background: '#fff', borderBottom: '0.5px solid var(--wx-line)' }}>
          {[{ k: 'list', l: '候选人列表 (' + candidateList.length + ')' }, { k: 'match', l: 'AI 匹配度' }, { k: 'compare', l: '对比' }].map(tb => (
            <div key={tb.k} className="grow center" onClick={() => setTab(tb.k)}
              style={{ padding: '12px 0', fontSize: 14, fontWeight: tab === tb.k ? 600 : 400, color: tab === tb.k ? 'var(--wx-green)' : 'var(--wx-text-gray)', borderBottom: tab === tb.k ? '2px solid var(--wx-green)' : '2px solid transparent', cursor: 'pointer' }}>
              {tb.l}
            </div>
          ))}
        </div>

        {/* 列表视图 */}
        {tab === 'list' && candidateList.map(cl => (
          <div key={cl.id} className="job-card" style={{ cursor: 'pointer' }}
            onClick={() => navigate('/recruiter/talent/' + cl.id)}>
            <div className="row" style={{ gap: 10 }}>
              <span className="avatar" style={{ width: 42, height: 42, borderRadius: 8, background: pickColor(cl.logoIdx), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, fontWeight: 600, flexShrink: 0 }}>{cl.name[0]}</span>
              <div className="grow" style={{ overflow: 'hidden' }}>
                <div className="row between">
                  <span style={{ fontWeight: 600, fontSize: 14 }}>{cl.name}{cl.virtual && <span className="tag tag-gray" style={{ marginLeft: 4, fontSize: 10 }}>虚拟</span>}</span>
                  <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--wx-green)', cursor: 'pointer', borderBottom: '1px dashed var(--wx-green)' }}
                    onClick={(e) => { e.stopPropagation(); setSelectedId(cl.id); setTab('match') }}
                    title="点击查看匹配度怎么算的">{cl.matchScore}<span style={{ fontSize: 10, fontWeight: 400 }}>%</span></span>
                </div>
                <div className="row gap6" style={{ marginTop: 4, flexWrap: 'wrap' }}>
                  {candidateTagNames(cl).length > 0
                    ? candidateTagNames(cl).map(tg => <span key={tg} className="tag tag-green" style={{ fontSize: 10, padding: '1px 6px' }}>{tg}</span>)
                    : <span className="tiny muted">{tagOptionsLoading ? '标签加载中...' : '暂无标签库标签'}</span>}
                </div>
                <div className="row between tiny muted" style={{ marginTop: 4 }}>
                  <span>应聘：{cl.job}</span>
                  <span>{cl.lastMsgTime} · 💬</span>
                </div>
              </div>
            </div>
            <div style={{ background: 'var(--wx-surface-2)', borderRadius: 4, height: 4, marginTop: 8, overflow: 'hidden' }}>
              <div style={{ width: cl.matchScore + '%', height: '100%', background: 'var(--wx-green)', borderRadius: 4 }} />
            </div>
          </div>
        ))}

        {/* 单人选匹配 */}
        {tab === 'match' && (<>
          <div className="row" style={{ background: '#fff', padding: '16px', gap: 12 }}>
            <span className="avatar" style={{ width: 50, height: 50, borderRadius: 8, background: pickColor(0), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 19, fontWeight: 600 }}>{c.name[0]}</span>
            <div className="grow">
              <div style={{ fontWeight: 600, fontSize: 16 }}>{c.name}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>应聘「{c.job}」</div>
              <div className="row gap6" style={{ marginTop: 6 }}>
                {candidateTagNames(c, 4).length > 0
                  ? candidateTagNames(c, 4).map(h => <span key={h} className="tag tag-green">{h}</span>)
                  : <span className="tiny muted">{tagOptionsLoading ? '标签加载中...' : '暂无标签库标签'}</span>}
              </div>
            </div>
          </div>
          <div className="center" style={{ background: '#fff', padding: '16px 0 4px' }}>
            <div className="tiny muted">AI 综合匹配度</div>
            <div style={{ fontSize: 40, fontWeight: 800, color: 'var(--wx-green)' }}>{c.score}<span style={{ fontSize: 16 }}>分</span></div>
            <RadarChart data={c.dims} size={240} />
          </div>
          <AICard title="AI 简历亮点摘要" tip="AI 分析结果，仅供参考">
            该候选人具备 5 年 React 开发经验，曾任前端技术负责人，与岗位核心要求匹配度 {c.score}%，互动积极、响应及时，建议优先沟通。
          </AICard>
          <div className="cell-group-title">分项得分</div>
          <div className="cell-group"><div style={{ padding: '14px 16px 4px' }}>
            {c.dims.map(d => <ScoreBar key={d.key} label={d.key} score={d.score} color={d.score >= 85 ? '#07C160' : '#FA9D3B'} />)}
          </div></div>
        </>)}

        {/* 候选人对比 */}
        {tab === 'compare' && (<>
          <div className="ai-tip padx" style={{ paddingTop: 12 }}>⚡ AI 多维度横向对比，匹配最高者标注「AI 推荐」</div>
          <div className="cell-group">
            {candidateCompare.map(p => (
              <div key={p.name} style={{ padding: '14px 16px', borderBottom: '0.5px solid var(--wx-line-light)' }}>
                <div className="row between" style={{ marginBottom: 8 }}>
                  <span style={{ fontWeight: 600 }}>{p.name}{p.best && <span className="tag tag-green" style={{ marginLeft: 6 }}>⚡AI推荐</span>}</span>
                  <span className="tiny muted">综合 {Math.round((p.skill + p.exp + p.salary + p.complete + p.active) / 5)}</span>
                </div>
                <ScoreBar label="技能匹配" score={p.skill} />
                <ScoreBar label="经验相关" score={p.exp} />
                <ScoreBar label="薪资匹配" score={p.salary} color="#FA9D3B" />
                <ScoreBar label="互动积极" score={p.active} />
              </div>
            ))}
          </div>
        </>)}

        <div className="btn-block-wrap row gap12">
          <button className="btn btn-default" onClick={() => setShowShare(true)}>转发推荐</button>
          <button className="btn btn-primary" onClick={() => navigate('/recruiter/chat/1')}>💬 发起沟通</button>
        </div>
      </div>
      <RecruiterBottomNav />
    </>
  )
}

/* ============ 数据统计详页（趋势 + AI 洞察 + 穿透） ============ */
export function RecruiterStats() {
  const navigate = useNavigate()
  const t = statTrend
  const [exchangeStats, setExchangeStats] = useState(null)
  const [exchangeStatsLoading, setExchangeStatsLoading] = useState(true)
  const [exchangeStatsError, setExchangeStatsError] = useState('')
  const [applicationStats, setApplicationStats] = useState(null)
  const [applicationStatsLoading, setApplicationStatsLoading] = useState(true)
  const [applicationStatsError, setApplicationStatsError] = useState('')
  const [jobStats, setJobStats] = useState([])
  const [jobStatsLoading, setJobStatsLoading] = useState(true)
  const [jobStatsError, setJobStatsError] = useState('')
  const [businessStats, setBusinessStats] = useState(null)
  const [businessStatsLoading, setBusinessStatsLoading] = useState(true)
  const [businessStatsError, setBusinessStatsError] = useState('')
  const [deepDiveStats, setDeepDiveStats] = useState(null)
  const [deepDiveStatsLoading, setDeepDiveStatsLoading] = useState(true)
  const [deepDiveStatsError, setDeepDiveStatsError] = useState('')

  useEffect(() => {
    let alive = true
    setDeepDiveStatsLoading(true)
    getRecruiterDeepDiveStats({ days: 7, limit: 5 })
      .then(data => {
        if (!alive) return
        setDeepDiveStats(data)
        setDeepDiveStatsError('')
      })
      .catch(error => {
        if (!alive) return
        setDeepDiveStats(null)
        setDeepDiveStatsError(error.message || '统计深化数据加载失败')
      })
      .finally(() => {
        if (alive) setDeepDiveStatsLoading(false)
      })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    let alive = true
    setBusinessStatsLoading(true)
    getRecruiterBusinessLoopStats()
      .then(data => {
        if (!alive) return
        setBusinessStats(data)
        setBusinessStatsError('')
      })
      .catch(error => {
        if (!alive) return
        setBusinessStats(null)
        setBusinessStatsError(error.message || '业务闭环统计加载失败')
      })
      .finally(() => {
        if (alive) setBusinessStatsLoading(false)
      })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    let alive = true
    setExchangeStatsLoading(true)
    getContactExchangeStats()
      .then(data => {
        if (!alive) return
        setExchangeStats(data)
        setExchangeStatsError('')
      })
      .catch(error => {
        if (!alive) return
        setExchangeStats(null)
        setExchangeStatsError(error.message || '对接统计加载失败')
      })
      .finally(() => {
        if (alive) setExchangeStatsLoading(false)
      })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    let alive = true
    setApplicationStatsLoading(true)
    getRecruiterApplicationStats()
      .then(data => {
        if (!alive) return
        setApplicationStats(data)
        setApplicationStatsError('')
      })
      .catch(error => {
        if (!alive) return
        setApplicationStats(null)
        setApplicationStatsError(error.message || '投递统计加载失败')
      })
      .finally(() => {
        if (alive) setApplicationStatsLoading(false)
      })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    let alive = true
    setJobStatsLoading(true)
    listMyJobs({ limit: 100 })
      .then(data => {
        if (!alive) return
        setJobStats(data.items || [])
        setJobStatsError('')
      })
      .catch(error => {
        if (!alive) return
        setJobStats([])
        setJobStatsError(error.message || '岗位浏览统计加载失败')
      })
      .finally(() => {
        if (alive) setJobStatsLoading(false)
      })
    return () => { alive = false }
  }, [])

  const summaryStats = deepDiveStats?.summary || businessStats
  const successfulConnections = summaryStats?.successful_connection_count ?? exchangeStats?.accepted_count ?? aggregateStats.totalExchanges
  const pendingConnections = summaryStats?.pending_exchange_count ?? exchangeStats?.pending_count ?? 0
  const declinedConnections = summaryStats?.declined_exchange_count ?? exchangeStats?.declined_count ?? 0
  const totalContactExchanges = summaryStats?.contact_exchange_count ?? exchangeStats?.total_count ?? aggregateStats.totalExchanges
  const statsLoading = deepDiveStatsLoading || businessStatsLoading || exchangeStatsLoading || applicationStatsLoading || jobStatsLoading
  const connectionDisplayValue = businessStatsLoading && exchangeStatsLoading ? '...' : successfulConnections
  const totalApplications = summaryStats?.application_count ?? applicationStats?.total_count ?? 0
  const applicationDisplayValue = businessStatsLoading && applicationStatsLoading ? '...' : totalApplications
  const realTotalViews = summaryStats?.view_count ?? jobStats.reduce((sum, job) => sum + Number(job.view_count || 0), 0)
  const viewDisplayValue = businessStatsLoading && jobStatsLoading ? '...' : realTotalViews
  const topViewedJobs = deepDiveStats?.top_jobs?.length > 0
    ? deepDiveStats.top_jobs.map(job => ({
      id: job.job_id,
      name: job.title,
      views: job.view_count || 0,
      applications: job.application_count || 0,
      connections: job.successful_connection_count || 0,
    }))
    : jobStats.length > 0
    ? [...jobStats]
      .sort((a, b) => Number(b.view_count || 0) - Number(a.view_count || 0))
      .slice(0, 5)
      .map(job => ({
        id: job.id,
        name: job.title,
        views: job.view_count || 0,
      }))
    : aggregateStats.topJobs
  const topKpis = [
    ['总浏览', viewDisplayValue, 'visitors', 1],
    ['岗位数', businessStatsLoading && jobStatsLoading ? '...' : (summaryStats?.job_count ?? jobStats.length), 'visitors', 1],
    ['收到投递', applicationDisplayValue, 'talent', null],
    ['有效对接', connectionDisplayValue, 'talent', null],
  ]
  const overviewKpis = [
    ['总浏览量', viewDisplayValue],
    ['总投递', applicationDisplayValue],
    ['有效对接', connectionDisplayValue],
    ['有效对接率', statsLoading ? '...' : `${summaryStats?.application_to_connection_rate ?? 0}%`],
  ]
  const trendPoints = deepDiveStats?.trend || []
  const trendLabels = trendPoints.length > 0 ? trendPoints.map(item => item.date.slice(5)) : t.days
  const viewTrend = trendPoints.length > 0 ? trendPoints.map(item => item.view_count || 0) : t.views
  const conversationTrend = trendPoints.length > 0 ? trendPoints.map(item => item.conversation_count || 0) : t.msgs
  const applicationTrend = trendPoints.length > 0 ? trendPoints.map(item => item.application_count || 0) : []

  return (
    <>
      <NavBar title="数据统计" />
      <div className="page">
        <div className="row" style={{ background: '#fff', padding: 16, gap: 0 }}>
          {topKpis.map(([label, value, target, param], index) => (
            <div
              key={index}
              className="grow center"
              style={{ cursor: 'pointer' }}
              onClick={() => target === 'visitors' ? navigate('/recruiter/job/visitors/' + param) : navigate('/recruiter/talent')}
            >
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--wx-blue)' }}>{value}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{label}</div>
            </div>
          ))}
        </div>

        <div className="cell-group-title">全岗位总览</div>
        {businessStatsError && (
          <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{businessStatsError}</div>
        )}
        {deepDiveStatsError && (
          <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-orange)' }}>{deepDiveStatsError}，趋势图将显示演示兜底数据。</div>
        )}
        <div className="row" style={{ background: '#fff', padding: '12px 16px', gap: 0, borderBottom: '0.5px solid var(--wx-line-light)' }}>
          {overviewKpis.map(([label, value], index) => (
            <div key={index} className="grow center">
              <div style={{ fontSize: 16, fontWeight: 700 }}>{value}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{label}</div>
            </div>
          ))}
        </div>

        <div className="cell-group-title">真实投递统计</div>
        <div className="cell-group">
          {applicationStatsError ? (
            <div className="cell">
              <span className="grow tiny" style={{ color: 'var(--wx-red)' }}>{applicationStatsError}</span>
            </div>
          ) : (
            <>
              <div className="cell">
                <span className="cell-label">投递总数</span>
                <span className="cell-value">{applicationStatsLoading ? '加载中...' : `${totalApplications} 条`}</span>
              </div>
              <div className="cell">
                <span className="cell-label">新投递</span>
                <span className="cell-value">{applicationStatsLoading ? '加载中...' : `${applicationStats?.submitted_count ?? 0} 条`}</span>
              </div>
              <div className="cell">
                <span className="cell-label">已查看</span>
                <span className="cell-value">{applicationStatsLoading ? '加载中...' : `${applicationStats?.viewed_count ?? 0} 条`}</span>
              </div>
              <div className="cell">
                <span className="cell-label">已邀面</span>
                <span className="cell-value">{applicationStatsLoading ? '加载中...' : `${applicationStats?.interview_invited_count ?? 0} 条`}</span>
              </div>
              <div className="cell">
                <span className="cell-label">已录用 / 已拒绝</span>
                <span className="cell-value">{applicationStatsLoading ? '加载中...' : `${applicationStats?.hired_count ?? 0} / ${applicationStats?.rejected_count ?? 0} 条`}</span>
              </div>
              <div style={{ padding: '0 16px 12px' }} className="tiny muted">
                数据来源：当前招聘者收到的真实投递记录，按 job_applications.status 汇总。
              </div>
            </>
          )}
        </div>

        <div className="cell-group-title">真实对接统计</div>
        <div className="cell-group">
          {exchangeStatsError ? (
            <div className="cell">
              <span className="grow tiny" style={{ color: 'var(--wx-red)' }}>{exchangeStatsError}</span>
            </div>
          ) : (
            <>
              <div className="cell">
                <span className="cell-label">成功对接</span>
                <span className="cell-value">{exchangeStatsLoading ? '加载中...' : `${successfulConnections} 次`}</span>
              </div>
              <div className="cell">
                <span className="cell-label">待确认交换</span>
                <span className="cell-value">{exchangeStatsLoading ? '加载中...' : `${pendingConnections} 次`}</span>
              </div>
              <div className="cell">
                <span className="cell-label">已拒绝交换</span>
                <span className="cell-value">{exchangeStatsLoading ? '加载中...' : `${declinedConnections} 次`}</span>
              </div>
              <div className="cell">
                <span className="cell-label">交换请求总数</span>
                <span className="cell-value">{exchangeStatsLoading ? '加载中...' : `${totalContactExchanges} 次`}</span>
              </div>
              <div style={{ padding: '0 16px 12px' }} className="tiny muted">
                统计口径：双方在聊天中完成联系方式交换，状态为 accepted 时计为一次有效对接。
              </div>
            </>
          )}
        </div>

        <div style={{ background: '#fff', padding: '8px 16px 12px', borderBottom: '8px solid var(--wx-bg)' }}>
          <button className="btn btn-weak btn-sm" style={{ width: '100%' }} onClick={() => navigate('/recruiter/funnel')}>
            查看招聘漏斗
          </button>
        </div>

        <div className="cell-group-title">岗位热度 TOP5（真实）</div>
        <div className="cell-group">
          {topViewedJobs.map((job, index) => (
            <div key={job.id} className="cell link" onClick={() => navigate('/recruiter/job/visitors/' + job.id)}>
              <span style={{ fontSize: 18, fontWeight: 700, marginRight: 10, color: index < 3 ? 'var(--wx-green)' : 'var(--wx-text-light)' }}>#{index + 1}</span>
              <span className="grow" style={{ fontSize: 14 }}>{job.name}</span>
              <span className="tiny muted">
                {job.views} 浏览{job.applications !== undefined ? ` / ${job.applications} 投递 / ${job.connections} 对接` : ''}
              </span>
              <span className="cell-arrow">›</span>
            </div>
          ))}
        </div>

        <div className="cell-group-title">近 7 天浏览趋势（真实）</div>
        <div className="cell-group"><div style={{ padding: '12px 8px' }}>
          <LineChart series={viewTrend} labels={trendLabels} />
        </div></div>

        <div className="cell-group-title">近 7 天沟通趋势（真实）</div>
        <div className="cell-group"><div style={{ padding: '12px 8px' }}>
          <LineChart series={conversationTrend} labels={trendLabels} color="#10AEFF" />
        </div></div>

        {applicationTrend.length > 0 && (
          <>
            <div className="cell-group-title">近 7 天投递趋势（真实）</div>
            <div className="cell-group"><div style={{ padding: '12px 8px' }}>
              <LineChart series={applicationTrend} labels={trendLabels} color="#FA9D3B" />
            </div></div>
          </>
        )}

        <div className="cell-group-title">AI 数据洞察（规则兜底）</div>
        {t.insights.map((insight, index) => (
          <AICard key={index} title={insight.phen} tip="演示洞察，仅供参考">
            <div>归因：{insight.cause}</div>
            <div style={{ marginTop: 4, color: 'var(--wx-green-dark)' }}>建议：{insight.advice}</div>
          </AICard>
        ))}
      </div>
      <RecruiterBottomNav />
    </>
  )
}

// END RecruiterStats (RecruiterBottomNav added at bottom)
