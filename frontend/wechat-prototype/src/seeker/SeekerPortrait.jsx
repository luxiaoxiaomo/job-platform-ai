import React, { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, AIBadge, AICard, useToast } from '../components/ui.jsx'
import { RadarChart, ScoreBar } from '../components/charts.jsx'
import { resumeParsed, seekerProfile } from '../mock/data.js'
import { useProfile } from '../common/ProfileContext.jsx'
import { uploadResume } from '../services/index.js'
import { getLegacyResumeStatus } from '../utils/resumeStatus.js'

export function SeekerResumeUpload() {
  const navigate = useNavigate()
  const toast = useToast()
  const fileInputRef = useRef(null)
  const { hasResume, resume, profile, markResume } = useProfile()
  const [stage, setStage] = useState(hasResume ? 'done' : 'idle')
  const [currentResume, setCurrentResume] = useState(resume)
  const [error, setError] = useState('')
  const profileSkills = inferProfileSkills(profile, currentResume?.parsed_snapshot)

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
              <span className="tiny" style={{ color: 'var(--wx-green-dark)', textDecoration: 'underline' }}>点击此处重新上传</span>
            </>)}
          </div>
          {error && <div className="ai-tip" style={{ marginTop: 10, color: 'var(--wx-red)' }}>{error}</div>}
        </div></div>

        {stage === 'done' && (<>
          <div className="ai-tip padx">当前为临时核心信息回写，正式简历解析模块后续再设计。</div>
          {currentResume?.parsed_snapshot && (
            <AICard title="投递快照">{currentResume.parsed_snapshot}</AICard>
          )}
          <div className="cell-group-title">基础信息回写结果</div>
          <div className="cell-group">
            <Row label="姓名" value={profile?.real_name || '暂未生成'} ai />
            <Row label="性别" value={profile?.gender || '暂未生成'} ai />
            <Row label="学历" value={profile?.education || '暂未生成'} ai />
            <Row label="经验" value={profile?.experience_years !== null && profile?.experience_years !== undefined ? `${profile.experience_years}年` : '暂未生成'} ai />
            <Row label="职业方向" value={profile?.target_position || '暂未生成'} ai />
          </div>
          <div className="cell-group-title">技能标签</div>
          <div className="cell-group"><div style={{ padding: 16 }}>
            {profileSkills.length > 0
              ? <div className="tagcloud">{profileSkills.map(s => <span key={s} className="tag tag-green" style={{ fontSize: 13, padding: '4px 12px' }}>{s}</span>)}</div>
              : <div className="tiny muted">暂未生成技能标签</div>}
          </div></div>
        </>)}
      </div>
      <div className="page-foot">
        {stage === 'done'
          ? <>
            <button className="btn btn-default" onClick={chooseFile}>重新上传</button>
            <button className="btn btn-primary" onClick={() => navigate('/seeker/portrait')}>查看我的简历画像</button>
          </>
          : <button className={`btn ${stage === 'uploading' ? 'btn-disabled' : 'btn-primary'}`} onClick={chooseFile}>{stage === 'uploading' ? '上传中...' : '选择并上传简历'}</button>}
      </div>
    </>
  )
}

function Row({ label, value, ai }) {
  return (
    <div className="cell"><span className="cell-label">{label}</span>
      <span className="cell-value">{value} {ai && <span className="ai-badge soft" style={{ marginLeft: 4 }}>临时回写</span>}</span>
    </div>
  )
}

function inferProfileSkills(profile, snapshot = '') {
  const source = [
    profile?.target_position || '',
    profile?.education || '',
    snapshot || '',
  ].join('\n')
  const keywords = ['PeopleSoft', 'HCM', '人事', '薪酬福利', '电子合同', '实施', '运维', '优化', '项目交付', '需求分析']
  return keywords.filter(keyword => source.includes(keyword))
}

export function SeekerPortrait() {
  const navigate = useNavigate()
  const { resume, profile } = useProfile()
  const p = seekerProfile
  const name = profile?.real_name || '未填写姓名'
  const target = profile?.target_position || p.level + '前端'
  const experience = profile?.experience_years !== null && profile?.experience_years !== undefined ? `${profile.experience_years}年经验` : '经验未填写'
  const education = profile?.education || '学历未填写'
  const city = profile?.city || '城市未填写'
  const status = getLegacyResumeStatus(resume)
  return (
    <>
      <NavBar title="我的简历画像" />
      <div className="page">
        <div className="portrait-hd">
          <div className="ph-name">{name} 的能力画像</div>
          <span className="ph-level">⚡ 当前方向：{target}</span>
        </div>

        {resume?.file_name && (
          <div className="cell-group">
            <div className="cell">
              <span className="cell-label">当前简历</span>
              <span className="cell-value">{resume.file_name}</span>
            </div>
            <div className="cell">
              <span className="cell-label">解析状态</span>
              <span className="cell-value">
                <span style={{
                  color: status.color === 'green' ? '#07C160' : status.color === 'orange' ? '#FA9D3B' : '#999',
                  fontWeight: 500
                }}>{status.label}</span>
              </span>
            </div>
          </div>
        )}

        <div className="cell-group-title">基础画像</div>
        <div className="cell-group"><div style={{ padding: 16 }}>
          <div className="tagcloud">
            {p.tags.map(t => <span key={t.t} className={`tc ${t.w}`}>{t.t}</span>)}
          </div>
          <div className="tiny muted" style={{ marginTop: 10 }}>基于简历关键词提取</div>
        </div></div>

        <div className="cell-group-title">能力维度参考</div>
        <div className="center" style={{ background: '#fff', paddingTop: 8 }}><RadarChart data={p.dims} size={240} /></div>
        <div className="cell-group"><div style={{ padding: '14px 16px 4px' }}>
          {p.dims.map(d => <ScoreBar key={d.key} label={d.key} score={d.score} color={d.score >= 85 ? '#07C160' : '#FA9D3B'} />)}
        </div></div>

        <div className="btn-block-wrap">
          <button className="btn btn-default" onClick={() => navigate('/seeker/resume')}>重新上传简历</button>
          <button className="btn btn-default" onClick={() => navigate('/seeker/parse-history')}>查看解析历史</button>
        </div>
      </div>
    </>
  )
}
