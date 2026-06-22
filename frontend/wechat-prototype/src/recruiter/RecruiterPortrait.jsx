import React from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { NavBar, AIBadge, AICard, useToast } from '../components/ui.jsx'
import { RadarChart, ScoreBar } from '../components/charts.jsx'
import { companyProfile, jobProfile, jdAttractiveness } from '../mock/data.js'
import { getCurrentUser } from '../services/index.js'
import { pickPublicTagNames, usePublicTagOptions } from '../common/usePublicTagOptions.js'

/* ============ 企业画像 ============ */
export function RecruiterCompanyPortrait() {
  const navigate = useNavigate()
  const toast = useToast()
  const [searchParams] = useSearchParams()
  const isFresh = searchParams.get('fresh') === 'true'
  const currentUser = getCurrentUser()
  const c = {
    ...companyProfile,
    name: currentUser?.display_name || companyProfile.name,
  }
  const { tagOptions, tagOptionsLoading } = usePublicTagOptions()
  const companyTagNames = pickPublicTagNames(tagOptions, 1, 6)

  return (
    <>
      <NavBar title="企业画像" right={<span onClick={() => toast('已刷新画像')}>刷新</span>} />
      <div className="page">
        {isFresh && (
          <div className="ai-tip padx" style={{ paddingTop: 10 }}>
            ✅ 注册完成！AI 已基于你的营业执照信息和行业自动生成初始企业画像，你可以查看下方画像并手动调整标签和评分。
          </div>
        )}
        <div className="portrait-hd">
          <div className="ph-name">{c.name}</div>
          <span className="ph-level">⚡ AI 生成的企业画像</span>
        </div>

        <AICard title="AI 企业画像总结" tip="AI 基于企业信息与岗位数据生成">{c.oneline}</AICard>

        <div className="cell-group-title">企业标签</div>
        <div className="cell-group"><div style={{ padding: 16 }}>
          <div className="tagcloud">
            {companyTagNames.length > 0
              ? companyTagNames.map(t => <span key={t} className="tag tag-green" style={{ fontSize: 13, padding: '5px 12px' }}>{t}</span>)
              : <span className="tiny muted">{tagOptionsLoading ? '标签加载中...' : '后台标签库暂无可用标签'}</span>}
          </div>
        </div></div>

        <div className="cell-group-title">企业维度评分</div>
        <div className="center" style={{ background: '#fff', paddingTop: 8 }}><RadarChart data={c.dims} size={240} color="#10AEFF" /></div>
        <div className="cell-group"><div style={{ padding: '14px 16px 4px' }}>
          {c.dims.map(d => <ScoreBar key={d.key} label={d.key} score={d.score} color={d.score >= 85 ? '#07C160' : '#FA9D3B'} />)}
        </div></div>

        <AICard title="AI 招聘建议">企业「技术氛围」「成长空间」评分突出，建议在岗位 JD 中强化这两点以吸引技术型候选人；「规模实力」相对一般，可用虚拟名 + 完整岗位信息策略平衡。</AICard>
      </div>
    </>
  )
}

/* ============ 岗位画像（可编辑） ============ */
export function RecruiterJobPortrait() {
  const navigate = useNavigate()
  const toast = useToast()
  const [searchParams] = useSearchParams()
  const isFresh = searchParams.get('fresh') === 'true'
  const j = jobProfile
  const { tagOptions, tagOptionsLoading } = usePublicTagOptions()
  const jobTagNames = pickPublicTagNames(tagOptions, 2, 8)

  return (
    <>
      <NavBar title="岗位画像" right={<span onClick={() => toast('已刷新画像')}>刷新</span>} />
      <div className="page">
        {isFresh && (
          <div className="ai-tip padx" style={{ paddingTop: 10 }}>
            ✅ 岗位发布成功！AI 已自动生成岗位画像（标签+维度评分），你可以查看下方画像并手动调整。
          </div>
        )}
        <div className="portrait-hd">
          <div className="ph-name">{j.name}</div>
          <span className="ph-level">⚡ AI 生成的岗位画像{isFresh ? '（可编辑）' : ''}</span>
        </div>

        <AICard title="AI 岗位画像总结" tip="AI 分析，仅供参考">{j.oneline}</AICard>

        <div className="cell-group-title">岗位标签（可编辑）</div>
        <div className="cell-group"><div style={{ padding: 16 }}>
          <div className="tagcloud" style={{ marginBottom: 8 }}>
            {jobTagNames.length > 0
              ? jobTagNames.map(t => <span key={t} className="tag tag-green" style={{ fontSize: 13, padding: '5px 12px' }}>{t}</span>)
              : <span className="tiny muted">{tagOptionsLoading ? '标签加载中...' : '后台标签库暂无可用标签'}</span>}
          </div>
          <div className="tiny muted">标签来自后台 base-data 标签库，发布岗位时保存统一 ID。</div>
        </div></div>

        <div className="cell-group-title">岗位维度</div>
        <div className="center" style={{ background: '#fff', paddingTop: 8 }}><RadarChart data={j.dims} size={240} /></div>
        <div className="cell-group"><div style={{ padding: '14px 16px 4px' }}>
          {j.dims.map(d => <ScoreBar key={d.key} label={d.key} score={d.score} color={d.score >= 85 ? '#07C160' : '#FA9D3B'} />)}
        </div></div>

        <AICard title="AI 优化建议">该岗位「岗位热度」高但「招聘紧急度」标记一般，建议适当置顶提升曝光；「学历要求」偏低有利于扩大候选池。岗位画像将用于二期的精准画像匹配推送。</AICard>

        {/* JD 吸引力分析 */}
        <div className="cell-group-title">⚡ AI JD 吸引力分析</div>
        <div className="cell-group"><div style={{ padding: 16 }}>
          <div className="row between" style={{ marginBottom: 10 }}>
            <span style={{ fontSize: 14 }}>综合吸引力评分</span>
            <span style={{ fontSize: 22, fontWeight: 800, color: jdAttractiveness.score >= 80 ? 'var(--wx-green)' : 'var(--wx-orange)' }}>
              {jdAttractiveness.score}<span style={{ fontSize: 12, fontWeight: 400 }}>分 · {jdAttractiveness.level}</span>
            </span>
          </div>
          {jdAttractiveness.factors.map(f => (
            <div key={f.key} style={{ marginBottom: 8 }}>
              <div className="row between tiny" style={{ marginBottom: 2 }}>
                <span>{f.good ? '✓' : '⚠'} {f.key}</span>
                <span style={{ color: f.good ? 'var(--wx-green)' : 'var(--wx-orange)' }}>{f.score}</span>
              </div>
              <div style={{ background: 'var(--wx-surface-2)', borderRadius: 3, height: 4, overflow: 'hidden' }}>
                <div style={{ width: f.score + '%', height: '100%', background: f.good ? 'var(--wx-green)' : 'var(--wx-orange)' }} />
              </div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{f.note}</div>
            </div>
          ))}
          <div style={{ marginTop: 10, padding: '8px 10px', background: '#FFF7E6', borderRadius: 6 }}>
            <div className="tiny" style={{ color: 'var(--wx-orange)', fontWeight: 600 }}>
              📉 你的浏览→留言转化率 {jdAttractiveness.benchmark.myConversion}%，低于平台均值 {jdAttractiveness.benchmark.avgConversion}%
            </div>
          </div>
        </div></div>

        <div className="cell-group-title">⚡ AI 优化建议</div>
        <div className="cell-group"><div style={{ padding: 16, lineHeight: 1.9 }}>
          {jdAttractiveness.suggestions.map((s, i) => (
            <div key={i} className="row gap6" style={{ alignItems: 'flex-start', marginBottom: 6 }}>
              <span style={{ color: 'var(--wx-green)' }}>{i + 1}.</span>
              <span className="tiny" style={{ lineHeight: 1.6 }}>{s}</span>
            </div>
          ))}
        </div></div>

        <div className="btn-block-wrap">
          <button className="btn btn-primary" onClick={() => navigate('/recruiter/candidate')}>查看匹配候选人</button>
        </div>
      </div>
    </>
  )
}
