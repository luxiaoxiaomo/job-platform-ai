import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, AIBadge } from '../components/ui.jsx'
import { RecruiterBottomNav } from './RecruiterBottomNav.jsx'
import {
  getContactExchangeStats,
  getRecruiterBusinessLoopStats,
  listMyJobs,
  listRecruiterApplications,
} from '../services/index.js'

const FUNNEL_COLORS = ['#E8F5FF', '#D0EBFF', '#A8D5FF', '#6BB6FF', '#3A9BFF', '#1373D9']
const FINAL_STATUSES = new Set(['interview_invited', 'hired'])
const PROCESSED_STATUSES = new Set(['viewed', 'interview_invited', 'rejected', 'hired'])

function toNumber(value) {
  const num = Number(value || 0)
  return Number.isFinite(num) ? num : 0
}

function getApplicationBuckets(applications) {
  return applications.reduce((acc, item) => {
    const jobId = String(item.job_id)
    if (!acc[jobId]) {
      acc[jobId] = {
        submitted: 0,
        processed: 0,
        interviews: 0,
        hired: 0,
      }
    }

    acc[jobId].submitted += 1
    if (PROCESSED_STATUSES.has(item.status)) acc[jobId].processed += 1
    if (FINAL_STATUSES.has(item.status)) acc[jobId].interviews += 1
    if (item.status === 'hired') acc[jobId].hired += 1
    return acc
  }, {})
}

function sumBuckets(buckets) {
  return Object.values(buckets).reduce((acc, item) => ({
    submitted: acc.submitted + item.submitted,
    processed: acc.processed + item.processed,
    interviews: acc.interviews + item.interviews,
    hired: acc.hired + item.hired,
  }), {
    submitted: 0,
    processed: 0,
    interviews: 0,
    hired: 0,
  })
}

function buildFunnel({ selectedJob, jobs, applicationsByJob }) {
  const allJobs = selectedJob === 'all'
    ? jobs
    : jobs.filter(job => String(job.id) === String(selectedJob))
  const appStats = selectedJob === 'all'
    ? sumBuckets(applicationsByJob)
    : applicationsByJob[String(selectedJob)] || { submitted: 0, processed: 0, interviews: 0, hired: 0 }
  const views = allJobs.reduce((sum, job) => sum + toNumber(job.view_count), 0)
  const conversations = allJobs.reduce((sum, job) => sum + toNumber(job.conversation_count), 0)
  const base = Math.max(views, conversations, appStats.submitted, 1)

  return [
    { stage: '岗位浏览', count: views, note: '求职者打开岗位详情', color: FUNNEL_COLORS[0] },
    { stage: '发起咨询', count: conversations, note: '求职者进入岗位会话', color: FUNNEL_COLORS[1] },
    { stage: '简历投递', count: appStats.submitted, note: '已提交真实简历', color: FUNNEL_COLORS[2] },
    { stage: '招聘者处理', count: appStats.processed, note: '已查看、邀约、拒绝或录用', color: FUNNEL_COLORS[3] },
    { stage: '面试邀约', count: appStats.interviews, note: '已邀约或进入录用链路', color: FUNNEL_COLORS[4] },
    { stage: '录用结果', count: appStats.hired, note: '状态为已录用', color: FUNNEL_COLORS[5] },
  ].map(item => ({
    ...item,
    rate: base > 0 ? Number(((item.count / base) * 100).toFixed(1)) : 0,
  }))
}

function getDropAdvice(funnel) {
  const [views, conversations, applications, processed] = funnel
  if (views.count > 0 && conversations.count / views.count < 0.08) {
    return '浏览到咨询转化偏低，优先检查岗位标题、薪资区间和 JD 亮点是否足够直接。'
  }
  if (conversations.count > 0 && applications.count / conversations.count < 0.25) {
    return '咨询后投递偏低，建议在会话中补充团队、面试流程和岗位硬性要求，减少候选人犹豫。'
  }
  if (applications.count > 0 && processed.count / applications.count < 0.5) {
    return '投递处理率偏低，建议优先处理新投递，避免候选人流失。'
  }
  return '当前漏斗没有明显单点断层，下一步可以关注访客穿透和高意向候选人跟进。'
}

export default function RecruiterFunnel() {
  const navigate = useNavigate()
  const [selectedJob, setSelectedJob] = useState('all')
  const [jobs, setJobs] = useState([])
  const [applications, setApplications] = useState([])
  const [exchangeStats, setExchangeStats] = useState(null)
  const [businessStats, setBusinessStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    setLoading(true)
    Promise.all([
      listMyJobs({ limit: 100 }),
      listRecruiterApplications({ limit: 100 }),
      getContactExchangeStats().catch(() => null),
      getRecruiterBusinessLoopStats().catch(() => null),
    ])
      .then(([jobData, applicationData, exchangeData, businessData]) => {
        if (!alive) return
        setJobs(jobData.items || [])
        setApplications(applicationData.items || [])
        setExchangeStats(exchangeData)
        setBusinessStats(businessData)
        setError('')
      })
      .catch(err => {
        if (!alive) return
        setError(err.message || '招聘漏斗加载失败')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })

    return () => { alive = false }
  }, [])

  const applicationsByJob = useMemo(() => getApplicationBuckets(applications), [applications])
  const funnel = useMemo(
    () => buildFunnel({ selectedJob, jobs, applicationsByJob }),
    [selectedJob, jobs, applicationsByJob],
  )
  const selectedJobData = jobs.find(job => String(job.id) === String(selectedJob))
  const jobName = selectedJob === 'all' ? '全部岗位' : selectedJobData?.title || `岗位 #${selectedJob}`
  const totalViews = funnel[0].count
  const totalConversations = funnel[1].count
  const totalApplications = funnel[2].count
  const acceptedExchanges = businessStats?.successful_connection_count ?? exchangeStats?.accepted_count ?? 0
  const exchangeTotal = businessStats?.contact_exchange_count ?? exchangeStats?.total_count ?? 0
  const advice = getDropAdvice(funnel)

  return (
    <>
      <NavBar title="招聘漏斗" />
      <div style={{ paddingBottom: 72 }}>
        <div style={{ padding: '12px 16px', background: 'var(--wx-bg)' }}>
          <div className="tiny muted" style={{ marginBottom: 8 }}>选择岗位</div>
          <div className="row gap8" style={{ overflowX: 'auto', flexWrap: 'nowrap' }}>
            <button
              className={`btn btn-sm ${selectedJob === 'all' ? 'btn-primary' : 'btn-weak'}`}
              onClick={() => setSelectedJob('all')}
              style={{ flexShrink: 0 }}
            >
              全部岗位
            </button>
            {jobs.slice(0, 8).map(job => (
              <button
                key={job.id}
                className={`btn btn-sm ${selectedJob === String(job.id) ? 'btn-primary' : 'btn-weak'}`}
                onClick={() => setSelectedJob(String(job.id))}
                style={{ flexShrink: 0, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                title={job.title}
              >
                {job.title}
              </button>
            ))}
          </div>
        </div>

        <div className="row" style={{ background: '#fff', padding: 16, gap: 0, borderBottom: '0.5px solid var(--wx-line-light)' }}>
          {[
            ['浏览', loading ? '...' : totalViews],
            ['咨询', loading ? '...' : totalConversations],
            ['投递', loading ? '...' : totalApplications],
            ['有效对接', loading ? '...' : acceptedExchanges],
          ].map(([label, value]) => (
            <div key={label} className="grow center">
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--wx-blue)' }}>{value}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{label}</div>
            </div>
          ))}
        </div>

        {error && (
          <div style={{ margin: '12px 16px', padding: 12, borderRadius: 8, background: '#FFF5F5', color: 'var(--wx-red)', fontSize: 13 }}>
            {error}
          </div>
        )}

        <div style={{ padding: '24px 16px', background: 'white' }}>
          <div className="row between" style={{ marginBottom: 16 }}>
            <span style={{ fontWeight: 600, fontSize: 15 }}>{jobName} · 真实转化漏斗</span>
            <AIBadge soft>真实数据</AIBadge>
          </div>

          {loading ? (
            <div className="center muted" style={{ padding: '32px 0', fontSize: 13 }}>加载中...</div>
          ) : (
            <div style={{ position: 'relative' }}>
              {funnel.map((item, idx) => {
                const width = Math.max(42, 100 - idx * 10)
                const nextItem = funnel[idx + 1]
                const conversion = nextItem && item.count > 0
                  ? ((nextItem.count / item.count) * 100).toFixed(1)
                  : null

                return (
                  <div key={item.stage} style={{ marginBottom: idx < funnel.length - 1 ? 16 : 0 }}>
                    <div
                      style={{
                        background: item.color,
                        borderRadius: 6,
                        padding: '12px 16px',
                        width: `${width}%`,
                        margin: '0 auto',
                        position: 'relative',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                      }}
                    >
                      <div className="row between">
                        <span style={{ fontWeight: 600, fontSize: 14 }}>{item.stage}</span>
                        <span style={{ fontWeight: 700, fontSize: 17, color: 'var(--wx-blue)' }}>{item.count}</span>
                      </div>
                      <div className="row between" style={{ marginTop: 4 }}>
                        <span className="tiny muted">{item.note}</span>
                        <span className="tiny" style={{ color: 'var(--wx-blue)' }}>{item.rate}%</span>
                      </div>
                    </div>

                    {conversion !== null && (
                      <div style={{ textAlign: 'center', padding: '6px 0' }}>
                        <div style={{ fontSize: 20, color: '#ccc', lineHeight: 1 }}>↓</div>
                        <div
                          className="tiny"
                          style={{ color: conversion >= 50 ? 'var(--wx-green-dark)' : conversion >= 20 ? 'var(--wx-orange)' : 'var(--wx-red)' }}
                        >
                          转化率 {conversion}%
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <div style={{ margin: '12px 16px', background: 'var(--ai-bg)', borderRadius: 8, padding: 14 }}>
          <div className="row gap8" style={{ marginBottom: 8 }}>
            <AIBadge>AI 洞察</AIBadge>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#3a5a48' }}>转化瓶颈分析</span>
          </div>
          <div className="tiny" style={{ lineHeight: 1.8, color: '#3a5a48' }}>
            {advice}
            <br />
            全部岗位联系方式交换 {exchangeTotal} 次，其中成功 {acceptedExchanges} 次；单岗位维度暂按投递与会话数据判断。
          </div>
        </div>

        <div className="cell-group-title">下一步动作</div>
        <div className="cell-group">
          <div className="cell" style={{ alignItems: 'flex-start', paddingTop: 12, paddingBottom: 12 }}>
            <div style={{ fontSize: 18, marginRight: 10 }}>JD</div>
            <div className="grow">
              <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>优化岗位吸引力</div>
              <div className="tiny muted" style={{ lineHeight: 1.6 }}>
                浏览高但咨询少时，优先补强薪资、职责边界、团队亮点和硬性要求。
              </div>
              <button className="btn btn-weak btn-sm" style={{ marginTop: 8 }} onClick={() => navigate('/recruiter/job-portrait')}>
                查看 JD 分析
              </button>
            </div>
          </div>
          <div className="cell" style={{ alignItems: 'flex-start', paddingTop: 12, paddingBottom: 12 }}>
            <div style={{ fontSize: 18, marginRight: 10 }}>HR</div>
            <div className="grow">
              <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>加快投递处理</div>
              <div className="tiny muted" style={{ lineHeight: 1.6 }}>
                新投递进入后尽快标记查看、邀约或拒绝，后续可接入提醒和团队协作。
              </div>
            </div>
          </div>
          <div className="cell" style={{ alignItems: 'flex-start', paddingTop: 12, paddingBottom: 12 }}>
            <div style={{ fontSize: 18, marginRight: 10 }}>AI</div>
            <div className="grow">
              <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>补齐访客穿透</div>
              <div className="tiny muted" style={{ lineHeight: 1.6 }}>
                当前已能看真实漏斗总量，下一阶段需要把访客明细、访问时间和高意向识别落到后端。
              </div>
            </div>
          </div>
        </div>
      </div>
      <RecruiterBottomNav />
    </>
  )
}
