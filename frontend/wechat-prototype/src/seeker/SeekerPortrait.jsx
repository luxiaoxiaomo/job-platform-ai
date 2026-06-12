import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, AIBadge, AICard, useToast } from '../components/ui.jsx'
import { RadarChart, ScoreBar } from '../components/charts.jsx'
import { resumeParsed, seekerProfile } from '../mock/data.js'
import { useProfile } from '../common/ProfileContext.jsx'

/* ============ 简历上传（上传 → AI 解析动画 → 预填） ============ */
export function SeekerResumeUpload() {
  const navigate = useNavigate()
  const toast = useToast()
  const { hasResume, markResume } = useProfile()
  const [stage, setStage] = useState(hasResume ? 'done' : 'idle') // idle | parsing | done
  const r = resumeParsed

  const upload = () => {
    setStage('parsing')
    setTimeout(() => { setStage('done'); markResume(); toast('简历解析完成', '✓') }, 1800)
  }

  return (
    <>
      <NavBar title="上传简历" />
      <div className="page" style={{ paddingBottom: 90 }}>
        <div className="cell-group-title">上传简历文件</div>
        <div className="cell-group"><div style={{ padding: 16 }}>
          <div className={`uploader ${stage === 'done' ? 'done' : ''}`} onClick={stage === 'idle' ? upload : undefined}>
            {stage === 'idle' && (<>
              <span style={{ fontSize: 34 }}>📄</span>
              <span style={{ fontSize: 14 }}>上传 PDF / 图片简历</span>
              <AIBadge soft>AI 自动解析</AIBadge>
            </>)}
            {stage === 'parsing' && (<>
              <span className="spin" style={{ width: 24, height: 24 }} />
              <span style={{ fontSize: 14 }}>AI 正在解析简历…</span>
              <span className="tiny muted">提取基本信息 / 工作经历 / 技能</span>
            </>)}
            {stage === 'done' && (<>
              <span style={{ fontSize: 30 }}>✅</span>
              <span style={{ fontSize: 14, color: 'var(--wx-green-dark)' }}>简历已解析，信息已自动填充</span>
            </>)}
          </div>
        </div></div>

        {stage === 'done' && (<>
          <div className="ai-tip padx">⚡ 以下信息由 AI 从简历解析，带「AI解析」标记，请核对</div>
          <div className="cell-group-title">基本信息</div>
          <div className="cell-group">
            <Row label="姓名" value={r.name} ai /><Row label="性别 / 年龄" value={`${r.gender} · ${r.age}岁`} ai />
            <Row label="学历" value={r.edu} ai /><Row label="经验" value={r.exp} ai />
            <Row label="院校 / 专业" value={`${r.school} · ${r.major}`} ai />
          </div>
          <div className="cell-group-title">工作经历</div>
          <div className="cell-group">
            {r.work.map((w, i) => (
              <div key={i} className="cell" style={{ alignItems: 'flex-start', flexDirection: 'column', gap: 2 }}>
                <div className="row between" style={{ width: '100%' }}><span style={{ fontWeight: 500 }}>{w.role} · {w.company}</span><span className="tiny muted">{w.period}</span></div>
                <span className="tiny muted">{w.desc}</span>
              </div>
            ))}
          </div>
          <div className="cell-group-title">技能标签（AI 提取）</div>
          <div className="cell-group"><div style={{ padding: 16 }}>
            <div className="tagcloud">{r.skills.map(s => <span key={s} className="tag tag-green" style={{ fontSize: 13, padding: '4px 12px' }}>{s}</span>)}</div>
          </div></div>

          {/* A9: AI 简历优化建议 */}
          <AICard title="⚡ AI 简历优化建议" tip="AI 分析，帮助你提升简历竞争力">
            <div style={{ lineHeight: 1.8, fontSize: 13 }}>
              <div>💡 建议补充项目量化成果（如"日活提升 30%"）</div>
              <div>💡 技能描述可补充版本号（如 React 18）以提升匹配精度</div>
              <div>💡 教育经历可增加 GPA 或排名信息</div>
            </div>
          </AICard>
        </>)}
      </div>
      <div className="page-foot">
        {stage === 'done'
          ? <button className="btn btn-primary" onClick={() => navigate('/seeker/portrait')}>查看我的简历画像</button>
          : <button className={`btn ${stage === 'parsing' ? 'btn-disabled' : 'btn-primary'}`} onClick={stage === 'idle' ? upload : undefined}>{stage === 'parsing' ? '解析中…' : '上传并解析'}</button>}
      </div>
    </>
  )
}

function Row({ label, value, ai }) {
  return (
    <div className="cell"><span className="cell-label">{label}</span>
      <span className="cell-value">{value} {ai && <span className="ai-badge soft" style={{ marginLeft: 4 }}>AI解析</span>}</span>
    </div>
  )
}

/* ============ 简历画像 ============ */
export function SeekerPortrait() {
  const navigate = useNavigate()
  const p = seekerProfile
  return (
    <>
      <NavBar title="我的简历画像" />
      <div className="page">
        <div className="portrait-hd">
          <div className="ph-name">李然 的能力画像</div>
          <span className="ph-level">⚡ AI 评定：{p.level}前端</span>
        </div>

        <AICard title="AI 一句话画像" tip="AI 分析，仅供参考">{p.oneline}</AICard>

        {/* A10: 薪酬测算 */}
        <AICard title="💰 AI 薪酬测算" tip="基于画像维度+市场数据综合测算，仅供参考">
          基于你的技能水平、5年经验、深圳地区，AI 测算你的市场薪酬约为 <b style={{ color: 'var(--wx-green-dark)', fontSize: 18 }}>{p.salaryEstimate?.low || 18}K - {p.salaryEstimate?.high || 28}K</b>／月
          <div className="tiny muted" style={{ marginTop: 4 }}>测算依据：{p.salaryEstimate?.basis || '深圳·前端开发·5年经验·本科'}</div>
        </AICard>

        <div className="cell-group-title">能力标签云</div>
        <div className="cell-group"><div style={{ padding: 16 }}>
          <div className="tagcloud">
            {p.tags.map(t => <span key={t.t} className={`tc ${t.w}`}>{t.t}</span>)}
          </div>
          <div className="ai-tip" style={{ marginTop: 10 }}>标签大小代表能力权重，由 AI 基于简历分析得出</div>
        </div></div>

        <div className="cell-group-title">能力维度</div>
        <div className="center" style={{ background: '#fff', paddingTop: 8 }}><RadarChart data={p.dims} size={240} /></div>
        <div className="cell-group"><div style={{ padding: '14px 16px 4px' }}>
          {p.dims.map(d => <ScoreBar key={d.key} label={d.key} score={d.score} color={d.score >= 85 ? '#07C160' : '#FA9D3B'} />)}
        </div></div>

        <AICard title="AI 提升建议">{p.suggest}</AICard>

        <div className="btn-block-wrap">
          <button className="btn btn-default" onClick={() => navigate('/seeker/resume')}>重新上传简历</button>
        </div>
      </div>
    </>
  )
}
