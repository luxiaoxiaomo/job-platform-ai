import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, AIBadge } from '../components/ui.jsx'
import { RecruiterBottomNav } from './RecruiterBottomNav.jsx'
import { recruitmentFunnel, funnelByJob, myJobs } from '../mock/data.js'

export default function RecruiterFunnel() {
  const navigate = useNavigate()
  const [selectedJob, setSelectedJob] = useState('all')

  const funnel = selectedJob === 'all' ? recruitmentFunnel : funnelByJob[selectedJob]
  const jobName = selectedJob === 'all' ? '全部岗位' : myJobs.find(j => j.id === parseInt(selectedJob))?.name

  return (<>
    <NavBar title="招聘漏斗" />
    <div style={{ paddingBottom: 60 }}>
      {/* 岗位选择 */}
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
          {myJobs.slice(0, 3).map(j => (
            <button
              key={j.id}
              className={`btn btn-sm ${selectedJob === String(j.id) ? 'btn-primary' : 'btn-weak'}`}
              onClick={() => setSelectedJob(String(j.id))}
              style={{ flexShrink: 0 }}
            >
              {j.name}
            </button>
          ))}
        </div>
      </div>

      {/* 漏斗可视化 */}
      <div style={{ padding: '24px 16px', background: 'white' }}>
        <div className="row between" style={{ marginBottom: 16 }}>
          <span style={{ fontWeight: 600, fontSize: 15 }}>{jobName} · 转化漏斗</span>
          <AIBadge soft>AI 分析</AIBadge>
        </div>

        <div style={{ position: 'relative' }}>
          {funnel.map((item, idx) => {
            const width = 100 - idx * 15 // 漏斗逐层收窄
            const nextRate = funnel[idx + 1]?.rate
            const conversion = nextRate ? ((nextRate / item.rate) * 100).toFixed(1) : null

            return (
              <div key={item.stage} style={{ marginBottom: idx < funnel.length - 1 ? 16 : 0 }}>
                {/* 漏斗块 */}
                <div
                  style={{
                    background: item.color,
                    borderRadius: 6,
                    padding: '12px 16px',
                    width: `${width}%`,
                    margin: '0 auto',
                    position: 'relative',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                  }}
                >
                  <div className="row between">
                    <span style={{ fontWeight: 600, fontSize: 14 }}>{item.stage}</span>
                    <span style={{ fontWeight: 600, fontSize: 16, color: 'var(--wx-blue)' }}>{item.count}</span>
                  </div>
                  <div className="row between" style={{ marginTop: 4 }}>
                    <span className="tiny muted">占浏览总数</span>
                    <span className="tiny" style={{ color: 'var(--wx-blue)' }}>{item.rate}%</span>
                  </div>
                </div>

                {/* 转化率箭头 */}
                {conversion && (
                  <div style={{ textAlign: 'center', padding: '6px 0' }}>
                    <div style={{ fontSize: 20, color: '#ccc' }}>↓</div>
                    <div className="tiny" style={{ color: conversion >= 50 ? 'var(--wx-green-dark)' : conversion >= 20 ? 'var(--wx-orange)' : 'var(--wx-red)' }}>
                      转化率 {conversion}%
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* AI 洞察 */}
      <div style={{ margin: '12px 16px', background: 'var(--ai-bg)', borderRadius: 8, padding: 14 }}>
        <div className="row gap8" style={{ marginBottom: 8 }}>
          <AIBadge>AI 洞察</AIBadge>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#3a5a48' }}>转化瓶颈分析</span>
        </div>
        <div className="tiny" style={{ lineHeight: 1.8, color: '#3a5a48' }}>
          • 浏览→留言转化率 {funnel[1].rate.toFixed(1)}%，{funnel[1].rate < 15 ? '低于' : funnel[1].rate > 20 ? '高于' : '接近'}行业均值 18%<br/>
          • 留言→深度沟通转化率 {((funnel[2].rate / funnel[1].rate) * 100).toFixed(1)}%，建议优先跟进高意向候选人<br/>
          • 面试→录用转化率 {((funnel[4].rate / funnel[3].rate) * 100).toFixed(1)}%，{((funnel[4].rate / funnel[3].rate) * 100) < 25 ? '可能存在面试流程问题' : '表现良好'}
        </div>
      </div>

      {/* 优化建议 */}
      <div className="cell-group-title">优化建议</div>
      <div className="cell-group">
        <div className="cell" style={{ alignItems: 'flex-start', paddingTop: 12, paddingBottom: 12 }}>
          <div style={{ fontSize: 20, marginRight: 10 }}>💡</div>
          <div className="grow">
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>提升 JD 吸引力</div>
            <div className="tiny muted" style={{ lineHeight: 1.6 }}>
              浏览→留言转化偏低，建议优化岗位描述、补充亮点信息
            </div>
            <button className="btn btn-weak btn-sm" style={{ marginTop: 8 }} onClick={() => navigate('/recruiter/job-portrait')}>
              查看 JD 分析
            </button>
          </div>
        </div>
        <div className="cell" style={{ alignItems: 'flex-start', paddingTop: 12, paddingBottom: 12 }}>
          <div style={{ fontSize: 20, marginRight: 10 }}>⚡</div>
          <div className="grow">
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>加快响应速度</div>
            <div className="tiny muted" style={{ lineHeight: 1.6 }}>
              高意向候选人平均等待回复时间 18 小时，建议 4 小时内响应
            </div>
          </div>
        </div>
        <div className="cell" style={{ alignItems: 'flex-start', paddingTop: 12, paddingBottom: 12 }}>
          <div style={{ fontSize: 20, marginRight: 10 }}>🎯</div>
          <div className="grow">
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>精准推荐候选人</div>
            <div className="tiny muted" style={{ lineHeight: 1.6 }}>
              使用「选人标准配置」提升匹配精度，减少无效沟通
            </div>
          </div>
        </div>
      </div>
    </div>
    <RecruiterBottomNav />
  </>)
}
