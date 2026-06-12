import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, AIBadge, AICard, useToast } from '../components/ui.jsx'
import { RecruiterBottomNav } from './RecruiterBottomNav.jsx'
import { RadarChart, LineChart, ScoreBar } from '../components/charts.jsx'
import { candidateMatch, candidateCompare, candidateList, statTrend, aggregateStats, myJobs, pickColor } from '../mock/data.js'
import { ShareSheet } from '../seeker/SeekerExtra.jsx'

/* ============ 候选人分析（列表 + 单人选匹配 + 对比） ============ */
export function RecruiterCandidate() {
  const navigate = useNavigate()
  const toast = useToast()
  const [tab, setTab] = useState('list') // list | match | compare
  const [selectedId, setSelectedId] = useState(null)
  const [showShare, setShowShare] = useState(false)
  const c = candidateMatch

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
                  {cl.tags.map(tg => <span key={tg} className="tag tag-green" style={{ fontSize: 10, padding: '1px 6px' }}>{tg}</span>)}
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
              <div className="row gap6" style={{ marginTop: 6 }}>{c.highlights.map(h => <span key={h} className="tag tag-green">{h}</span>)}</div>
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
  return (
    <>
      <NavBar title="数据统计" />
      <div className="page">
        <div className="row" style={{ background: '#fff', padding: 16, gap: 0 }}>
          {[
            ['总浏览', aggregateStats.totalViews, 'visitors', 1],
            ['独立访客', aggregateStats.totalUV, 'visitors', 1],
            ['收到留言', aggregateStats.totalMsgs, 'visitors', 1],
            ['对接成功', aggregateStats.totalExchanges, 'talent', null],
          ].map(([k, v, target, param], i) => (
            <div key={i} className="grow center" style={{ cursor: 'pointer' }}
              onClick={() => target === 'visitors' ? navigate('/recruiter/job/visitors/' + param) : navigate('/recruiter/talent')}>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--wx-blue)' }}>{v}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{k} ›</div>
            </div>
          ))}
        </div>

        {/* 总体统计看板 */}
        <div className="cell-group-title">📊 全岗位总览</div>
        <div className="row" style={{ background: '#fff', padding: '12px 16px', gap: 0, borderBottom: '0.5px solid var(--wx-line-light)' }}>
          {[['总浏览量', aggregateStats.totalViews], ['总留言', aggregateStats.totalMsgs], ['对接成功', aggregateStats.totalExchanges], ['平均匹配度', aggregateStats.avgMatch + '%']].map(([k, v], i) => (
            <div key={i} className="grow center">
              <div style={{ fontSize: 16, fontWeight: 700 }}>{v}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{k}</div>
            </div>
          ))}
        </div>
        <div style={{ background: '#fff', padding: '8px 16px 12px', borderBottom: '8px solid var(--wx-bg)' }}>
          <button className="btn btn-weak btn-sm" style={{ width: '100%' }} onClick={() => navigate('/recruiter/funnel')}>
            📈 查看招聘漏斗
          </button>
        </div>
        {/* 热度 TOP5 */}
        <div className="cell-group-title">岗位热度 TOP5</div>
        <div className="cell-group">
          {aggregateStats.topJobs.map((j, i) => (
            <div key={j.id} className="cell link" onClick={() => navigate('/recruiter/job/visitors/' + j.id)}>
              <span style={{ fontSize: 18, fontWeight: 700, marginRight: 10, color: i < 3 ? 'var(--wx-green)' : 'var(--wx-text-light)' }}>#{i + 1}</span>
              <span className="grow" style={{ fontSize: 14 }}>{j.name}</span>
              <span className="tiny muted">👁 {j.views}</span>
              <span className="cell-arrow">›</span>
            </div>
          ))}
        </div>

        <div className="cell-group-title">近 7 天浏览趋势</div>
        <div className="cell-group"><div style={{ padding: '12px 8px' }}>
          <LineChart series={t.views} labels={t.days} />
        </div></div>

        <div className="cell-group-title">近 7 天留言趋势</div>
        <div className="cell-group"><div style={{ padding: '12px 8px' }}>
          <LineChart series={t.msgs} labels={t.days} color="#10AEFF" />
        </div></div>

        <div className="cell-group-title">⚡ AI 数据洞察</div>
        {t.insights.map((ins, i) => (
          <AICard key={i} title={ins.phen} tip="AI 分析，仅供参考">
            <div>归因：{ins.cause}</div>
            <div style={{ marginTop: 4, color: 'var(--wx-green-dark)' }}>建议：{ins.advice}</div>
          </AICard>
        ))}
      </div>
      <RecruiterBottomNav />
    </>
  )
}
// END RecruiterStats (RecruiterBottomNav added at bottom)
