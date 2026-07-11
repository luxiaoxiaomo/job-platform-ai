import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, AICard } from '../components/ui.jsx'
import { RecruiterBottomNav } from './RecruiterBottomNav.jsx'
import { LineChart } from '../components/charts.jsx'
import { statTrend, aggregateStats } from '../mock/data.js'
import { getContactExchangeStats, getRecruiterApplicationStats, getRecruiterBusinessLoopStats, getRecruiterDeepDiveStats, listMyJobs, listRecruiterApplications } from '../services/index.js'
import { applicationStatusTag, applicationStatusText, formatDateTime } from '../utils/applicationView.js'

/* ============ 候选人分析（真实投递） ============ */
export function RecruiterCandidate() {
  const navigate = useNavigate()
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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
        setError(err.message || '候选人列表加载失败')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => { alive = false }
  }, [])

  const total = applications.length
  const submitted = applications.filter(item => item.status === 'submitted').length
  const active = applications.filter(item => ['viewed', 'interview_invited'].includes(item.status)).length
  const hired = applications.filter(item => item.status === 'hired').length

  return (
    <>
      <NavBar title="候选人分析" />
      <div className="page" style={{ paddingBottom: 80 }}>
        <div className="row" style={{ background: '#fff', padding: '16px', gap: 0 }}>
          {[
            ['总候选', loading ? '...' : total],
            ['新投递', loading ? '...' : submitted],
            ['沟通中', loading ? '...' : active],
            ['已录用', loading ? '...' : hired],
          ].map(([label, value]) => (
            <div key={label} className="grow center">
              <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{label}</div>
            </div>
          ))}
        </div>

        <div className="cell-group-title">真实投递候选人</div>
        {loading && <div className="ai-tip" style={{ margin: 16 }}>正在读取真实投递...</div>}
        {error && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>}
        <div className="cell-group">
          {!loading && !error && applications.length === 0 && (
            <div className="cell"><span className="grow tiny muted">暂无真实候选人投递</span></div>
          )}
          {!loading && !error && applications.map(application => (
            <div
              key={application.id}
              className="cell link"
              onClick={() => navigate('/recruiter/applications/' + application.id, { state: { application } })}
              style={{ alignItems: 'flex-start' }}
            >
              <span className="avatar" style={{ width: 40, height: 40, borderRadius: 8, background: 'var(--wx-green-bg)', color: 'var(--wx-green-dark)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15, fontWeight: 700, marginRight: 10, flexShrink: 0 }}>
                {(application.seeker_display_name || '候')[0]}
              </span>
              <div className="grow" style={{ minWidth: 0 }}>
                <div className="row between" style={{ gap: 8 }}>
                  <span style={{ fontWeight: 600, fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {application.seeker_display_name || `候选人 #${application.seeker_id}`}
                  </span>
                  <span className={`tag ${applicationStatusTag[application.status] || 'tag-gray'}`} style={{ fontSize: 11, flexShrink: 0 }}>
                    {applicationStatusText[application.status] || application.status}
                  </span>
                </div>
                <div className="tiny muted" style={{ marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {application.job_title || `岗位 #${application.job_id}`} {application.job_city ? `· ${application.job_city}` : ''}
                </div>
                <div className="tiny muted" style={{ marginTop: 4 }}>投递时间：{formatDateTime(application.created_at)}</div>
                {application.resume_snapshot && (
                  <div className="tiny" style={{ marginTop: 6, lineHeight: 1.6, color: 'var(--wx-text-2)' }}>{application.resume_snapshot}</div>
                )}
              </div>
              <span className="cell-arrow">›</span>
            </div>
          ))}
        </div>

        <div className="btn-block-wrap">
          <button className="btn btn-primary" onClick={() => navigate('/recruiter/talent')}>进入完整人才池</button>
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
