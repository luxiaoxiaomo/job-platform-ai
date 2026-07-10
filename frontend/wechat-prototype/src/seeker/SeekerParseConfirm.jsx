import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, HomeNavLink } from '../components/ui.jsx'
import { useProfile } from '../common/ProfileContext.jsx'
import { getStructuredResult, confirmStructuredResult } from '../services/resumes.js'
import { listPublicTagLibraryItems } from '../services/baseData.js'

export function SeekerParseConfirm() {
  const navigate = useNavigate()
  const { parseRunId } = useParams()
  const { refreshProfile, refreshResume } = useProfile()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [editingField, setEditingField] = useState(null) // 当前编辑的字段
  const [tagOptions, setTagOptions] = useState([])
  const [selectedTagIds, setSelectedTagIds] = useState([])
  const [tagOptionsLoading, setTagOptionsLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    // 调用真实 API
    getStructuredResult(parseRunId)
      .then(result => {
        setData(result)
        setError('')
        setSelectedTagIds((result.profile?.tag_refs || []).map(item => String(item.id)))
        setLoading(false)
      })
      .catch(err => {
        console.error('获取结构化结果失败:', err)
        setData(null)
        setError(err.message || '解析结果不存在')
        setLoading(false)
      })
  }, [parseRunId])

  useEffect(() => {
    let alive = true
    setTagOptionsLoading(true)
    listPublicTagLibraryItems({ limit: 100 })
      .then(result => {
        if (alive) setTagOptions(result.items || [])
      })
      .catch(() => {
        if (alive) setTagOptions([])
      })
      .finally(() => {
        if (alive) setTagOptionsLoading(false)
      })
    return () => { alive = false }
  }, [])

  const toggleTag = (id) => {
    const key = String(id)
    setSelectedTagIds(current => current.includes(key)
      ? current.filter(item => item !== key)
      : [...current, key])
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.85) return '#07C160' // 绿
    if (confidence >= 0.70) return '#FA9D3B' // 橙
    return '#FA5151' // 红
  }

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.85) return '✓'
    if (confidence >= 0.70) return '⚠️'
    return '❌'
  }

  const handleConfirm = async () => {
    try {
      await confirmStructuredResult(parseRunId, {
        structured_json: data.profile?.structured_json,
        tag_ids: selectedTagIds.map(id => Number(id)),
        min_confidence: 0,
      })
      await Promise.all([
        refreshProfile().catch(() => null),
        refreshResume().catch(() => null),
      ])
      alert('确认成功，结构化数据已保存')
      navigate('/seeker/portrait')
    } catch (err) {
      console.error('确认失败:', err)
      alert('确认失败: ' + (err.message || '未知错误'))
    }
  }

  if (loading) {
    return (
      <>
        <NavBar title="解析结果确认" right={<HomeNavLink />} />
        <div className="page" style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>加载中…</div>
      </>
    )
  }

  if (!data) {
    return (
      <>
        <NavBar title="解析结果确认" right={<HomeNavLink />} />
        <div className="page" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
          <div style={{ color: '#999' }}>{error || '解析结果不存在'}</div>
          <button className="btn btn-default" style={{ marginTop: 20, width: 'auto', padding: '0 24px' }}
            onClick={() => navigate('/seeker/parse-history')}>返回历史列表</button>
        </div>
      </>
    )
  }

  // 适配后端 R-P2 结构，同时兼容旧 mock 字段。
  const rawBasic = data.basic_info || data.basic || data.profile?.structured_json?.basic || {}
  const basic = normalizeBasic(rawBasic)
  const educations = normalizeRows(data.educations || data.profile?.structured_json?.education || [])
  const workExperiences = normalizeRows(data.work_experiences || data.profile?.structured_json?.work_experiences || [])
  const projects = normalizeRows(data.projects || data.profile?.structured_json?.projects || [])
  const skills = normalizeRows(data.skills || data.profile?.structured_json?.skills || [])
  const certificates = normalizeRows(data.certificates || data.profile?.structured_json?.certificates || [])

  const completedCount = Object.values(basic).filter(f => f && f.value).length
  const totalCount = Object.keys(basic).length

  return (
    <>
      <NavBar title="解析结果确认" right={<HomeNavLink />} />
      <div className="page" style={{ paddingBottom: 80 }}>

        {/* 顶部状态栏 */}
        <div style={{ background: '#F7F8FA', padding: '16px', marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 15, fontWeight: 600 }}>解析完成</span>
            <span style={{ fontSize: 13, color: '#07C160' }}>✓ 已成功</span>
          </div>
          <div style={{ fontSize: 12, color: '#999', marginBottom: 8 }}>
            解析时间: {data.profile?.created_at ? new Date(data.profile.created_at).toLocaleString('zh-CN') : data.uploadedAt ? new Date(data.uploadedAt).toLocaleString('zh-CN') : '-'}
          </div>
          <div style={{ fontSize: 13, color: '#576B95' }}>
            字段完整度: {completedCount}/{totalCount} 已确认
          </div>
        </div>

        {/* 原文预览（可折叠）*/}
        {data.extractedText && (
          <>
            <div className="cell-group-title">原文预览</div>
            <div className="cell-group" style={{ marginBottom: 12 }}>
              <div style={{ padding: '12px 16px' }}>
                <div style={{
                  maxHeight: 150,
                  overflow: 'auto',
                  background: '#F7F8FA',
                  padding: 12,
                  borderRadius: 8,
                  fontSize: 12,
                  lineHeight: 1.8,
                  whiteSpace: 'pre-wrap',
                  color: '#666'
                }}>
                  {data.extractedText}
                </div>
              </div>
            </div>
          </>
        )}

        {/* 基础信息 */}
        <div className="cell-group-title">基础信息</div>
        <div className="cell-group" style={{ marginBottom: 12 }}>
          {Object.entries(basic).map(([key, field]) => {
            if (!field) return null
            return (
              <div key={key} className="cell">
                <span className="cell-label" style={{ fontSize: 13 }}>{fieldLabels[key] || key}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ color: field.confirmed ? '#333' : '#999', fontSize: 14 }}>
                    {field.value ?? '-'}
                  </span>
                  {field.confidence !== undefined && (
                    <span style={{ fontSize: 14, color: getConfidenceColor(field.confidence) }}>
                      {getConfidenceLabel(field.confidence)}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* 教育经历 */}
        {educations.length > 0 && (
          <>
            <div className="cell-group-title">教育经历 ({educations.length} 条)</div>
            <div className="cell-group" style={{ marginBottom: 12 }}>
              {educations.map((edu, idx) => (
                <div key={idx} style={{ padding: '12px 16px', borderBottom: idx < educations.length - 1 ? '1px solid #eee' : 'none' }}>
                  <div style={{ fontWeight: 500, marginBottom: 6 }}>{edu.school_name} · {edu.major}</div>
                  <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>
                    {edu.degree} | {edu.start_date} ~ {edu.end_date}
                  </div>
                  {edu.confidence !== undefined && (
                    <div style={{ fontSize: 12, color: getConfidenceColor(edu.confidence) }}>
                      置信度: {Math.round(edu.confidence * 100)}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {/* 工作经历 */}
        {workExperiences.length > 0 && (
          <>
            <div className="cell-group-title">工作经历 ({workExperiences.length} 条)</div>
            <div className="cell-group" style={{ marginBottom: 12 }}>
              {workExperiences.map((work, idx) => (
                <div key={idx} style={{ padding: '12px 16px', borderBottom: idx < workExperiences.length - 1 ? '1px solid #eee' : 'none' }}>
                  <div style={{ fontWeight: 500, marginBottom: 6 }}>{work.company_name} · {work.position}</div>
                  <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>
                    {work.start_date} ~ {work.end_date}
                  </div>
                  {work.description && (
                    <div style={{ fontSize: 13, color: '#666', marginBottom: 6, lineHeight: 1.6 }}>
                      {work.description}
                    </div>
                  )}
                  {work.confidence !== undefined && (
                    <div style={{ fontSize: 12, color: getConfidenceColor(work.confidence) }}>
                      置信度: {Math.round(work.confidence * 100)}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {/* 项目经历 */}
        {projects.length > 0 && (
          <>
            <div className="cell-group-title">项目经历 ({projects.length} 条)</div>
            <div className="cell-group" style={{ marginBottom: 12 }}>
              {projects.map((proj, idx) => (
                <div key={idx} style={{ padding: '12px 16px' }}>
                  <div style={{ fontWeight: 500, marginBottom: 6 }}>{proj.project_name} · {proj.role}</div>
                  <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>
                    {proj.start_date} ~ {proj.end_date}
                  </div>
                  {proj.description && (
                    <div style={{ fontSize: 13, color: '#666', marginBottom: 6 }}>
                      {proj.description}
                    </div>
                  )}
                  {proj.confidence !== undefined && (
                    <div style={{ fontSize: 12, color: getConfidenceColor(proj.confidence) }}>
                      置信度: {Math.round(proj.confidence * 100)}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {/* 技能 */}
        {skills.length > 0 && (
          <>
            <div className="cell-group-title">技能 ({skills.length} 项)</div>
            <div className="cell-group" style={{ marginBottom: 12 }}>
              <div style={{ padding: '12px 16px' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {skills.map((skill, idx) => (
                    <div key={idx} style={{
                      padding: '6px 12px',
                      background: '#F7F8FA',
                      borderRadius: 16,
                      fontSize: 13,
                      border: skill.confidence ? `1px solid ${getConfidenceColor(skill.confidence)}` : '1px solid #e5e5e5'
                    }}>
                      {skill.skill_name} {skill.skill_level && `· ${skill.skill_level}`}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        <div className="cell-group-title">画像标签</div>
        <div className="cell-group" style={{ marginBottom: 12 }}>
          <div style={{ padding: '12px 16px' }}>
            <div style={{ fontSize: 12, color: '#999', marginBottom: 8 }}>
              {tagOptionsLoading ? '标签加载中...' : '从后台标签库选择，用于候选人搜索筛选。'}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {tagOptions.map(tag => {
                const active = selectedTagIds.includes(String(tag.id))
                return (
                  <button
                    key={tag.id}
                    type="button"
                    className={`tag ${active ? 'tag-green' : 'tag-gray'}`}
                    style={{ border: 0, cursor: 'pointer', fontSize: 12 }}
                    onClick={() => toggleTag(tag.id)}
                  >
                    {tag.name}
                  </button>
                )
              })}
            </div>
            {!tagOptionsLoading && tagOptions.length === 0 && (
              <div className="tiny muted" style={{ marginTop: 8 }}>暂无可用标签，请先在后台标签库维护。</div>
            )}
          </div>
        </div>

        {/* 证书 */}
        {certificates.length > 0 && (
          <>
            <div className="cell-group-title">证书 ({certificates.length} 项)</div>
            <div className="cell-group" style={{ marginBottom: 12 }}>
              {certificates.map((cert, idx) => (
                <div key={idx} className="cell">
                  <span className="cell-label">{cert.certificate_name}</span>
                  <span style={{ fontSize: 12, color: '#999' }}>{cert.certificate_type}</span>
                </div>
              ))}
            </div>
          </>
        )}

        {/* 底部操作按钮 */}
        <div className="btn-block-wrap">
          <button className="btn btn-default" onClick={() => navigate('/seeker/parse-history')}>暂不确认</button>
          <button className="btn btn-primary" onClick={handleConfirm}>确认并保存</button>
        </div>
      </div>
    </>
  )
}

const fieldLabels = {
  real_name: '姓名',
  gender: '性别',
  phone: '手机号',
  email: '邮箱',
  highest_education: '最高学历',
  work_years: '工作年限',
  current_city: '当前城市',
  target_position: '目标岗位',
}

function normalizeBasic(raw) {
  const source = raw || {}
  const fields = {
    real_name: source.real_name ?? source.name,
    gender: source.gender,
    phone: source.phone,
    email: source.email,
    highest_education: source.highest_education ?? source.education,
    work_years: source.work_years ?? source.experience_years,
    current_city: source.current_city ?? source.city,
    target_position: source.target_position ?? source.apply_job,
    expected_salary: source.expected_salary,
  }
  const confidence = source.confidence ?? source.confidence_score
  return Object.fromEntries(
    Object.entries(fields)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => [key, {
        value,
        confirmed: true,
        confidence,
      }])
  )
}

function normalizeRows(rows) {
  return (rows || []).map(row => ({
    ...row,
    confidence: row.confidence ?? row.confidence_score,
  }))
}
