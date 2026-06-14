import React, { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, AIBadge, AICard, useToast } from '../components/ui.jsx'
import { RadarChart, ScoreBar } from '../components/charts.jsx'
import { resumeParsed, seekerProfile } from '../mock/data.js'
import { useProfile } from '../common/ProfileContext.jsx'
import { uploadResume } from '../services/index.js'

export function SeekerResumeUpload() {
  const navigate = useNavigate()
  const toast = useToast()
  const fileInputRef = useRef(null)
  const { hasResume, resume, markResume } = useProfile()
  const [stage, setStage] = useState(hasResume ? 'done' : 'idle')
  const [currentResume, setCurrentResume] = useState(resume)
  const [error, setError] = useState('')
  const r = resumeParsed

  const chooseFile = () => {
    if (stage === 'uploading') return
    fileInputRef.current?.click()
  }

  const onFileChange = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    setStage('uploading')
    setError('')
    try {
      const uploaded = await uploadResume(file)
      setCurrentResume(uploaded)
      markResume(uploaded)
      setStage('done')
      toast('简历已上传', '✓')
    } catch (err) {
      setStage(hasResume ? 'done' : 'idle')
      setError(err.message || '简历上传失败')
      toast(err.message || '简历上传失败')
    }
  }

  return (
    <>
      <NavBar title="上传简历" />
      <div className="page" style={{ paddingBottom: 90 }}>
        <div className="cell-group-title">上传简历文件</div>
        <div className="cell-group"><div style={{ padding: 16 }}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.webp,.bmp"
            style={{ display: 'none' }}
            onChange={onFileChange}
          />
          <div className={`uploader ${stage === 'done' ? 'done' : ''}`} onClick={chooseFile}>
            {stage === 'idle' && (<>
              <span style={{ fontSize: 34 }}>📄</span>
              <span style={{ fontSize: 14 }}>上传 PDF / Word / Excel / 图片简历</span>
              <AIBadge soft>规则解析</AIBadge>
            </>)}
            {stage === 'uploading' && (<>
              <span className="spin" style={{ width: 24, height: 24 }} />
              <span style={{ fontSize: 14 }}>正在上传简历...</span>
              <span className="tiny muted">上传完成后会生成投递快照</span>
            </>)}
            {stage === 'done' && (<>
              <span style={{ fontSize: 30 }}>✓</span>
              <span style={{ fontSize: 14, color: 'var(--wx-green-dark)' }}>简历已上传，可用于投递</span>
              {currentResume?.file_name && <span className="tiny muted">{currentResume.file_name}</span>}
            </>)}
          </div>
          {error && <div className="ai-tip" style={{ marginTop: 10, color: 'var(--wx-red)' }}>{error}</div>}
        </div></div>

        {stage === 'done' && (<>
          <div className="ai-tip padx">⚡ 当前先用规则生成简历快照，后续接入 AI 精细解析。</div>
          {currentResume?.parsed_snapshot && (
            <AICard title="投递快照">{currentResume.parsed_snapshot}</AICard>
          )}
          <div className="cell-group-title">示例解析信息</div>
          <div className="cell-group">
            <Row label="姓名" value={r.name} ai /><Row label="性别 / 年龄" value={`${r.gender} · ${r.age}岁`} ai />
            <Row label="学历" value={r.edu} ai /><Row label="经验" value={r.exp} ai />
            <Row label="院校 / 专业" value={`${r.school} · ${r.major}`} ai />
          </div>
          <div className="cell-group-title">技能标签</div>
          <div className="cell-group"><div style={{ padding: 16 }}>
            <div className="tagcloud">{r.skills.map(s => <span key={s} className="tag tag-green" style={{ fontSize: 13, padding: '4px 12px' }}>{s}</span>)}</div>
          </div></div>
        </>)}
      </div>
      <div className="page-foot">
        {stage === 'done'
          ? <button className="btn btn-primary" onClick={() => navigate('/seeker/portrait')}>查看我的简历画像</button>
          : <button className={`btn ${stage === 'uploading' ? 'btn-disabled' : 'btn-primary'}`} onClick={chooseFile}>{stage === 'uploading' ? '上传中...' : '选择并上传简历'}</button>}
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

export function SeekerPortrait() {
  const navigate = useNavigate()
  const { resume } = useProfile()
  const p = seekerProfile
  return (
    <>
      <NavBar title="我的简历画像" />
      <div className="page">
        <div className="portrait-hd">
          <div className="ph-name">李然 的能力画像</div>
          <span className="ph-level">⚡ AI 评定：{p.level}前端</span>
        </div>

        {resume?.file_name && (
          <div className="cell-group">
            <div className="cell">
              <span className="cell-label">当前简历</span>
              <span className="cell-value">{resume.file_name}</span>
            </div>
          </div>
        )}

        <AICard title="AI 一句话画像" tip="AI 分析，仅供参考">{p.oneline}</AICard>

        <AICard title="💰 AI 薪酬测算" tip="基于画像维度+市场数据综合测算，仅供参考">
          基于你的技能水平、5年经验、深圳地区，AI 测算你的市场薪酬约为 <b style={{ color: 'var(--wx-green-dark)', fontSize: 18 }}>{p.salaryEstimate?.low || 18}K - {p.salaryEstimate?.high || 28}K</b> / 月
          <div className="tiny muted" style={{ marginTop: 4 }}>测算依据：{p.salaryEstimate?.basis || '深圳 · 前端开发 · 5年经验 · 本科'}</div>
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
