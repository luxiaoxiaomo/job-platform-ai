import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, AIBadge, AICard, useToast } from '../components/ui.jsx'
import { RecruiterBottomNav } from './RecruiterBottomNav.jsx'
import { ScoreBar } from '../components/charts.jsx'
import { getJobVisitors, myJobs, pickColor } from '../mock/data.js'

/* ============ 浏览量穿透：某岗位的访客列表 ============ */
export function RecruiterVisitors() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const job = myJobs.find(j => String(j.id) === String(jobId)) || myJobs[0]
  const visitors = getJobVisitors(jobId)
  const [sort, setSort] = useState('match') // match | views | time
  const [selected, setSelected] = useState(new Set())

  const sorted = [...visitors].sort((a, b) => {
    if (sort === 'match') return b.matchScore - a.matchScore
    if (sort === 'views') return b.views - a.views
    return 0
  })

  const toggle = (id) => setSelected(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })
  const inviteAll = () => {
    const count = selected.size || sorted.length
    toast(`已对 ${count} 人发起邀请沟通`, '📨')
  }

  return (
    <>
      <NavBar title="访客详情" />
      <div className="page has-tabbar">
        {/* 头部概览 */}
        <div style={{ background: '#fff', padding: '12px 16px', borderBottom: '0.5px solid var(--wx-line-light)' }}>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>{job.name}</div>
          <div className="row gap12 tiny muted">
            <span>👁 {job.views} 次浏览</span>
            <span>👤 {job.uv} 人看过</span>
            <span>💬 {job.msgs} 人留言</span>
          </div>
        </div>

        {/* 排序 + 操作 */}
        <div className="row between" style={{ background: '#fff', padding: '8px 16px', borderBottom: '0.5px solid var(--wx-line-light)' }}>
          <div className="row gap6">
            {[{ k: 'match', l: '按匹配度' }, { k: 'views', l: '按浏览次数' }].map(s => (
              <span key={s.k} className={`tag ${sort === s.k ? 'tag-green' : 'tag-gray'}`}
                style={{ cursor: 'pointer', fontSize: 12 }}
                onClick={() => setSort(s.k)}>{s.l}</span>
            ))}
          </div>
          <span className="tiny" style={{ color: 'var(--wx-green-dark)', cursor: 'pointer' }} onClick={() => { toast('全选模式') }}>全选</span>
        </div>

        {/* 访客列表 */}
        <div className="cell-group" style={{ marginTop: 0 }}>
          {sorted.map(v => (
            <div key={v.id} className="cell" style={{ alignItems: 'flex-start', padding: '12px 16px' }}>
              <span style={{ marginRight: 10, fontSize: 18, color: selected.has(v.id) ? 'var(--wx-green)' : 'var(--wx-text-light)', flexShrink: 0 }}
                onClick={(e) => { e.stopPropagation(); toggle(v.id) }}>
                {selected.has(v.id) ? '☑' : '☐'}
              </span>
              <span className="avatar" style={{ width: 40, height: 40, borderRadius: 8, background: pickColor(v.id), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15, fontWeight: 600, marginRight: 10, flexShrink: 0, cursor: 'pointer' }}
                onClick={() => navigate('/recruiter/talent/' + v.id)}>{v.name[0]}</span>
              <div className="grow" style={{ overflow: 'hidden' }}>
                <div className="row between">
                  <span style={{ fontWeight: 500, cursor: 'pointer' }} onClick={() => navigate('/recruiter/talent/' + v.id)}>{v.name}{v.virtual && <span className="tag tag-gray" style={{ marginLeft: 4, fontSize: 10 }}>虚拟名</span>}</span>
                  <span className="tag tag-green" style={{ fontSize: 12 }}>匹配 {v.matchScore}%</span>
                </div>
                <div className="row gap6" style={{ marginTop: 4, flexWrap: 'wrap' }}>
                  {v.tags.map(t => <span key={t} className="tag tag-green" style={{ fontSize: 10, padding: '1px 6px' }}>{t}</span>)}
                </div>
                <div className="row between tiny muted" style={{ marginTop: 4 }}>
                  <span>浏览 {v.views} 次 · {v.lastView}</span>
                  <span>{v.hasChatted ? '💬 已沟通' : '未互动'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {visitors.length === 0 && (
          <div className="empty" style={{ paddingTop: 80 }}><span className="tiny muted">暂无访客数据</span></div>
        )}

        <AICard title="AI 访客洞察" tip="AI 分析，仅供参考">
          浏览该岗位的 {visitors.length} 人中，{visitors.filter(v => v.hasChatted).length} 人已主动留言。AI 匹配度 ≥ 80% 的有 {visitors.filter(v => v.matchScore >= 80).length} 人，建议优先邀请沟通。
        </AICard>
      </div>

      <div className="page-foot">
        <button className="btn btn-primary" onClick={inviteAll}>
          📨 对 {selected.size || sorted.length} 人批量邀请沟通
        </button>
      </div>
      <RecruiterBottomNav />
    </>
  )
}
