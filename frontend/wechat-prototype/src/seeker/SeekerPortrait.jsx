import React, { useRef, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, HomeNavLink, AIBadge, AICard, useToast } from '../components/ui.jsx'
import { uploadResume, getStructuredResult, getProfileSummary } from '../services/index.js'
import { useProfile } from '../common/ProfileContext.jsx'
import { usePublicTagOptions } from '../common/usePublicTagOptions.js'

export function SeekerResumeUpload() {
  const navigate = useNavigate()
  const toast = useToast()
  const fileInputRef = useRef(null)
  const { hasResume, resume, profile, markResume } = useProfile()
  const [stage, setStage] = useState(hasResume ? 'done' : 'idle')
  const [currentResume, setCurrentResume] = useState(resume)
  const [currentParseRunId, setCurrentParseRunId] = useState(resume?.current_parse_run_id || null)
  const [parsedBasic, setParsedBasic] = useState(null)
  const [error, setError] = useState('')
  const { tagOptions, tagOptionsLoading } = usePublicTagOptions()
  const profileSkills = inferProfileSkills(profile, currentResume?.parsed_snapshot, parsedBasic, tagOptions)

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
      const parseRunId = uploaded.parse_run?.id || uploaded.current_parse_run_id
      setCurrentParseRunId(parseRunId || null)
      if (parseRunId) {
        const structured = await getStructuredResult(parseRunId).catch(() => null)
        setParsedBasic(normalizeStructuredBasic(structured?.basic_info || structured?.profile?.structured_json?.basic))
      } else {
        setParsedBasic(null)
      }
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
      <NavBar title="上传简历" right={<HomeNavLink />} />
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
          <div className="ai-tip padx">以下为本次上传简历的解析结果，确认后才会保存到个人资料。</div>
          {currentResume?.parsed_snapshot && (
            <AICard title="投递快照">{currentResume.parsed_snapshot}</AICard>
          )}
          <div className="cell-group-title">本次解析结果</div>
          <div className="cell-group">
            <Row label="姓名" value={parsedBasic?.real_name || '暂未识别'} ai />
            <Row label="年龄" value={parsedBasic?.age ? `${parsedBasic.age}岁` : '暂未识别'} ai />
            <Row label="性别" value={parsedBasic?.gender || '暂未识别'} ai />
            <Row label="学历" value={parsedBasic?.highest_education || '暂未识别'} ai />
            <Row label="经验" value={parsedBasic?.work_years !== null && parsedBasic?.work_years !== undefined ? `${parsedBasic.work_years}年` : '暂未识别'} ai />
            <Row label="职业方向" value={parsedBasic?.target_position || '暂未识别'} ai />
          </div>
          <div className="cell-group-title">技能标签</div>
          <div className="cell-group"><div style={{ padding: 16 }}>
            {profileSkills.length > 0
              ? <div className="tagcloud">{profileSkills.map(s => <span key={s} className="tag tag-green" style={{ fontSize: 13, padding: '4px 12px' }}>{s}</span>)}</div>
              : <div className="tiny muted">{tagOptionsLoading ? '标签加载中...' : '暂无匹配的标签库标签'}</div>}
          </div></div>
        </>)}
      </div>
      <div className="page-foot">
        {stage === 'done'
          ? <>
            <button className="btn btn-default" onClick={chooseFile}>重新上传</button>
            <button
              className={`btn ${currentParseRunId ? 'btn-primary' : 'btn-disabled'}`}
              onClick={() => currentParseRunId && navigate(`/seeker/parse-confirm/${currentParseRunId}`)}
            >
              确认并保存解析结果
            </button>
          </>
          : <button className={`btn ${stage === 'uploading' ? 'btn-disabled' : 'btn-primary'}`} onClick={chooseFile}>{stage === 'uploading' ? '上传中...' : '选择并上传简历'}</button>}
      </div>
    </>
  )
}

function Row({ label, value, ai }) {
  return (
    <div className="cell"><span className="cell-label">{label}</span>
      <span className="cell-value">{value} {ai && <span className="ai-badge soft" style={{ marginLeft: 4 }}>本次解析</span>}</span>
    </div>
  )
}

function inferProfileSkills(profile, snapshot = '', parsedBasic = null, tagOptions = []) {
  const source = [
    parsedBasic?.target_position || '',
    parsedBasic?.highest_education || '',
    profile?.target_position || '',
    profile?.education || '',
    snapshot || '',
  ].join('\n')
  return (tagOptions || [])
    .map(tag => tag?.name)
    .filter(Boolean)
    .filter(name => source.includes(name))
    .slice(0, 8)
}

function normalizeStructuredBasic(basic) {
  if (!basic) return null

  // 辅助函数：提取字段值（支持 P2 的 {value, confidence} 结构）
  const extractValue = (field) => {
    if (!field) return null
    // P2 格式: {value: "xxx", confidence: 0.9}
    if (typeof field === 'object' && 'value' in field) {
      return field.value
    }
    // 扁平格式: 直接是值
    return field
  }

  return {
    real_name: extractValue(basic.real_name) || extractValue(basic.name) || null,
    age: extractValue(basic.age) ?? null,
    gender: extractValue(basic.gender) || null,
    highest_education: extractValue(basic.highest_education) || extractValue(basic.education) || null,
    work_years: extractValue(basic.work_years) ?? extractValue(basic.experience_years) ?? null,
    target_position: extractValue(basic.target_position) || extractValue(basic.apply_job) || null,
  }
}

export function SeekerPortrait() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)

  useEffect(() => {
    getProfileSummary()
      .then(result => {
        setData(result)
        setLoading(false)
      })
      .catch(err => {
        console.error('获取画像数据失败:', err)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <>
        <NavBar title="我的简历画像" right={<HomeNavLink />} />
        <div className="page" style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>加载中…</div>
      </>
    )
  }

  // 空状态：未上传简历
  if (!data?.resume) {
    return (
      <>
        <NavBar title="我的简历画像" right={<HomeNavLink />} />
        <div className="page" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📄</div>
          <div style={{ color: '#999', marginBottom: 20 }}>还未上传简历</div>
          <button className="btn btn-primary" onClick={() => navigate('/seeker/resume')}>立即上传简历</button>
        </div>
      </>
    )
  }

  const { resume, profile, basic_info, summaries, completeness, review } = data
  const name = basic_info?.real_name || '未识别'
  const target = basic_info?.target_position || '求职中'
  const profileTagRefs = profile?.tag_refs || []

  return (
    <>
      <NavBar title="我的简历画像" right={<HomeNavLink />} />
      <div className="page">
        <div className="portrait-hd">
          <div className="ph-name">{name} 的简历画像</div>
          <span className="ph-level">⚡ 目标岗位：{target}</span>
        </div>

        {/* 简历文件信息 */}
        <div className="cell-group">
          <div className="cell">
            <span className="cell-label">当前简历</span>
            <span className="cell-value">{resume.file_name}</span>
          </div>
          <div className="cell">
            <span className="cell-label">解析状态</span>
            <span className="cell-value">
              <span style={{
                color: review.needs_review ? '#FA9D3B' : '#07C160',
                fontWeight: 500
              }}>{review.status_label}</span>
            </span>
          </div>
          {profile?.created_at && (
            <div className="cell">
              <span className="cell-label">解析时间</span>
              <span className="cell-value tiny muted">
                {new Date(profile.created_at).toLocaleString('zh-CN')}
              </span>
            </div>
          )}
        </div>

        {/* 待确认提示 */}
        {review.needs_review && (
          <div style={{ padding: '12px 16px', background: '#FFF7E6', margin: '12px 0', borderRadius: 8 }}>
            <div style={{ fontSize: 14, color: '#D46B08', marginBottom: 8 }}>
              ⚠️ 有 {review.low_confidence_count} 个字段待确认
            </div>
            <button
              className="btn btn-primary"
              style={{ width: '100%', padding: '8px' }}
              onClick={() => navigate(`/seeker/parse-confirm/${profile.parse_run_id}`)}
            >
              前往确认解析结果
            </button>
          </div>
        )}

        {/* 字段完整度 */}
        <div className="cell-group-title">字段完整度</div>
        <div className="cell-group">
          <div style={{ padding: '12px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: 14 }}>核心信息</span>
              <span style={{ fontSize: 20, fontWeight: 600, color: completeness.score >= 80 ? '#07C160' : '#FA9D3B' }}>
                {completeness.score}%
              </span>
            </div>
            <div style={{
              height: 8,
              background: '#F0F0F0',
              borderRadius: 4,
              overflow: 'hidden',
              marginBottom: 8
            }}>
              <div style={{
                width: `${completeness.score}%`,
                height: '100%',
                background: completeness.score >= 80 ? '#07C160' : '#FA9D3B',
                transition: 'width 0.3s'
              }} />
            </div>
            <div className="tiny muted">
              已填写 {completeness.filled_count}/{completeness.total_count} 个核心字段
            </div>
            {completeness.missing_fields?.length > 0 && (
              <div className="tiny" style={{ marginTop: 8, color: '#FA9D3B' }}>
                缺失字段: {completeness.missing_fields.join('、')}
              </div>
            )}
          </div>
        </div>

        {/* 基础信息 */}
        {basic_info && (
          <>
            <div className="cell-group-title">基础信息</div>
            <div className="cell-group">
              {basic_info.real_name && <div className="cell"><span className="cell-label">姓名</span><span className="cell-value">{basic_info.real_name}</span></div>}
              {basic_info.gender && <div className="cell"><span className="cell-label">性别</span><span className="cell-value">{basic_info.gender}</span></div>}
              {basic_info.age && <div className="cell"><span className="cell-label">年龄</span><span className="cell-value">{basic_info.age}岁</span></div>}
              {basic_info.highest_education && <div className="cell"><span className="cell-label">学历</span><span className="cell-value">{basic_info.highest_education}</span></div>}
              {basic_info.work_years !== null && basic_info.work_years !== undefined && (
                <div className="cell"><span className="cell-label">工作经验</span><span className="cell-value">{basic_info.work_years}年</span></div>
              )}
              {basic_info.current_city && <div className="cell"><span className="cell-label">当前城市</span><span className="cell-value">{basic_info.current_city}</span></div>}
              {basic_info.target_position && <div className="cell"><span className="cell-label">目标岗位</span><span className="cell-value">{basic_info.target_position}</span></div>}
            </div>
          </>
        )}

        {/* 技能标签 */}
        {profileTagRefs.length > 0 && (
          <>
            <div className="cell-group-title">画像标签</div>
            <div className="cell-group">
              <div style={{ padding: '12px 16px' }}>
                <div className="tagcloud">
                  {profileTagRefs.map(tag => (
                    <span key={tag.id} className="tag tag-green" style={{ fontSize: 13, padding: '4px 12px' }}>
                      {tag.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {summaries.skills?.length > 0 && (
          <>
            <div className="cell-group-title">技能 ({summaries.skills.length} 项)</div>
            <div className="cell-group">
              <div style={{ padding: '12px 16px' }}>
                <div className="tagcloud">
                  {summaries.skills.map((skill, idx) => (
                    <span key={idx} className="tag tag-green" style={{ fontSize: 13, padding: '4px 12px' }}>
                      {skill.skill_name}
                      {skill.skill_level && ` · ${skill.skill_level}`}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {/* 教育经历 */}
        {summaries.educations?.length > 0 && (
          <>
            <div className="cell-group-title">教育经历 ({summaries.educations.length} 条)</div>
            <div className="cell-group">
              {summaries.educations.map((edu, idx) => (
                <div key={idx} className="cell">
                  <span className="cell-label">{edu.degree}</span>
                  <span className="cell-value">{edu.school_name} · {edu.major}</span>
                </div>
              ))}
            </div>
          </>
        )}

        {/* 工作经历 */}
        {summaries.work_experiences?.length > 0 && (
          <>
            <div className="cell-group-title">工作经历 ({summaries.work_experiences.length} 条)</div>
            <div className="cell-group">
              {summaries.work_experiences.map((work, idx) => (
                <div key={idx} style={{ padding: '12px 16px', borderBottom: idx < summaries.work_experiences.length - 1 ? '1px solid #eee' : 'none' }}>
                  <div style={{ fontWeight: 500, marginBottom: 4 }}>
                    {work.position}
                    {work.company_name && ` @ ${work.company_name}`}
                  </div>
                  {work.description && (
                    <div className="tiny muted" style={{ lineHeight: 1.6 }}>
                      {work.description.length > 60 ? work.description.slice(0, 60) + '...' : work.description}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {/* 项目经历 */}
        {summaries.projects?.length > 0 && (
          <>
            <div className="cell-group-title">项目经历 ({summaries.projects.length} 条)</div>
            <div className="cell-group">
              {summaries.projects.map((proj, idx) => (
                <div key={idx} style={{ padding: '12px 16px', borderBottom: idx < summaries.projects.length - 1 ? '1px solid #eee' : 'none' }}>
                  <div style={{ fontWeight: 500, marginBottom: 4 }}>
                    {proj.project_name}
                    {proj.role && ` · ${proj.role}`}
                  </div>
                  {proj.description && (
                    <div className="tiny muted" style={{ lineHeight: 1.6 }}>
                      {proj.description.length > 60 ? proj.description.slice(0, 60) + '...' : proj.description}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {/* 证书 */}
        {summaries.certificates?.length > 0 && (
          <>
            <div className="cell-group-title">证书 ({summaries.certificates.length} 项)</div>
            <div className="cell-group">
              {summaries.certificates.map((cert, idx) => (
                <div key={idx} className="cell">
                  <span className="cell-label">{cert.certificate_name}</span>
                  <span className="cell-value tiny muted">{cert.certificate_type}</span>
                </div>
              ))}
            </div>
          </>
        )}

        {/* 底部按钮 */}
        <div className="btn-block-wrap">
          <button className="btn btn-default" onClick={() => navigate('/seeker/resume')}>重新上传简历</button>
          <button className="btn btn-default" onClick={() => navigate('/seeker/parse-history')}>查看解析历史</button>
        </div>
      </div>
    </>
  )
}
