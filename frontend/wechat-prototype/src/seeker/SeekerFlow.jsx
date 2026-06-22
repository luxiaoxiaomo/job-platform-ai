import React, { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, HomeNavLink, AIBadge, AICard, FormCell, useToast, Switch } from '../components/ui.jsx'
import { ShareSheet } from './SeekerExtra.jsx'
import { useProfile } from '../common/ProfileContext.jsx'
import { RealSeekerChat } from '../common/RealMessagePages.jsx'
import {
  addMyJobFavorite,
  getStructuredResult,
  listMyApplications,
  listMyJobFavorites,
  listPublicStandardPositions,
  listPublicTagLibraryItems,
  openJobConversation,
  removeMyJobFavorite,
  uploadResume,
} from '../services/index.js'
import { findPublicJobById } from '../utils/jobView.js'

function emptyJob(id) {
  return {
    id,
    name: `岗位 #${id}`,
    salary: '',
    city: '',
    exp: '',
    edu: '',
    tags: [],
    tagRefs: [],
    companyShow: '认证企业',
    aiHighlight: '岗位已通过平台审核。',
    duty: '',
    require: '',
    contactMethod: '平台内沟通',
  }
}

export function SeekerJobDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [job, setJob] = useState(emptyJob(id))
  const [jobError, setJobError] = useState('')
  const [applied, setApplied] = useState(false)
  const [fav, setFav] = useState(false)
  const [favoriteBusy, setFavoriteBusy] = useState(false)
  const [showShare, setShowShare] = useState(false)
  const { unlocked, completed, hasResume } = useProfile()

  useEffect(() => {
    let alive = true
    findPublicJobById(id)
      .then(realJob => {
        if (!alive) return
        setJob(realJob || emptyJob(id))
        setJobError(realJob ? '' : '未找到真实公开岗位。')
      })
      .catch(error => {
        if (!alive) return
        setJob(emptyJob(id))
        setJobError(error.message || '公开岗位加载失败。')
      })
    return () => { alive = false }
  }, [id])

  useEffect(() => {
    let alive = true
    listMyApplications({ limit: 100 })
      .then(data => {
        if (!alive) return
        setApplied((data.items || []).some(item => String(item.job_id) === String(job.id)))
      })
      .catch(() => {
        if (alive) setApplied(false)
      })
    return () => { alive = false }
  }, [job.id])

  useEffect(() => {
    let alive = true
    if (!Number(job.id)) {
      setFav(false)
      return () => { alive = false }
    }
    listMyJobFavorites({ limit: 100 })
      .then(data => {
        if (!alive) return
        setFav((data.items || []).some(item => String(item.job?.id) === String(job.id)))
      })
      .catch(() => {
        if (alive) setFav(false)
      })
    return () => { alive = false }
  }, [job.id])

  const tryViewFull = () => {
    navigate('/seeker/profile/edit?from=job&id=' + job.id)
  }

  const startConversation = async () => {
    if (!unlocked) {
      tryViewFull()
      return
    }
    try {
      const conversation = await openJobConversation({ job_id: Number(job.id) })
      navigate('/seeker/chat/' + conversation.id)
    } catch (error) {
      toast(error.message || '打开对话失败')
    }
  }

  const toggleFavorite = async () => {
    if (favoriteBusy) return
    if (!Number(job.id)) {
      toast('当前不是后端真实岗位，无法收藏')
      return
    }
    setFavoriteBusy(true)
    try {
      if (fav) {
        await removeMyJobFavorite(job.id)
        setFav(false)
        toast('已取消收藏')
      } else {
        await addMyJobFavorite(job.id)
        setFav(true)
        toast('已收藏')
      }
    } catch (error) {
      toast(error.message || '收藏失败')
    } finally {
      setFavoriteBusy(false)
    }
  }

  return (
    <>
      <NavBar title="职位详情" right={<><HomeNavLink /><span onClick={() => setShowShare(true)}>分享</span></>} />
      {showShare && <ShareSheet title="分享职位给好友" onClose={() => setShowShare(false)} />}
      <div className="page" style={{ paddingBottom: 80 }}>
        {jobError && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{jobError}</div>}

        <div style={{ background: '#fff', padding: 16 }}>
          <div className="row between">
            <span style={{ fontSize: 20, fontWeight: 700 }}>{job.name}</span>
            <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--wx-orange)' }}>{job.salary}</span>
          </div>
          <div className="jc-meta" style={{ marginTop: 10 }}>
            {job.city && <span className="tag tag-gray">{job.city}</span>}
            {job.exp && <span className="tag tag-gray">{job.exp}</span>}
            {job.edu && <span className="tag tag-gray">{job.edu}</span>}
          </div>
          {((job.tagRefs || []).length > 0 ? job.tagRefs.map(tag => tag.name) : (job.tags || [])).map(tag => (
            <span key={tag} className="tag tag-green" style={{ marginRight: 6 }}>{tag}</span>
          ))}
          <div className="row gap6" style={{ background: 'var(--ai-bg)', borderRadius: 6, padding: '8px 10px', marginTop: 12 }}>
            <AIBadge>AI亮点</AIBadge>
            <span className="tiny" style={{ color: '#3a5a48' }}>{job.aiHighlight}</span>
          </div>
        </div>

        <div className="cell-group" style={{ marginTop: 10 }}>
          <div className="cell link" onClick={() => navigate(`/seeker/company-portrait?recruiterId=${job.recruiterId || ''}`)}>
            <span className="jc-logo" style={{ marginRight: 10 }}>{job.companyShow?.[0] || '企'}</span>
            <div className="grow">
              <div style={{ fontWeight: 500 }}>{job.companyShow}</div>
              <div className="tiny muted">已通过企业认证 <span style={{ color: 'var(--wx-green-dark)', marginLeft: 6 }}>查看画像</span></div>
            </div>
          </div>
        </div>

        <div className="cell-group-title">工作职责</div>
        <div className="cell-group">
          <div style={{ padding: 16, whiteSpace: 'pre-line', lineHeight: 1.8, fontSize: 14 }}>{job.duty || '暂无岗位职责说明。'}</div>
        </div>

        {unlocked && (
          <>
            <div className="cell-group-title">任职要求</div>
            <div className="cell-group"><div style={{ padding: 16, whiteSpace: 'pre-line', lineHeight: 1.8, fontSize: 14 }}>{job.require || '暂无任职要求说明。'}</div></div>
            <div className="cell-group-title">联系方式</div>
            <div className="cell-group"><div className="cell"><span className="cell-label">联系方式</span><span className="cell-value">{job.contactMethod}</span></div></div>
          </>
        )}

        {!unlocked && (
          <div className="ai-card center">
            <div className="ai-card-bd">
              查看完整信息与投递需要完善资料：
              <div style={{ textAlign: 'left', padding: '6px 16px', fontSize: 13, lineHeight: 1.8 }}>
                {!completed && <div style={{ color: 'var(--wx-red)' }}>补全个人信息</div>}
                {!hasResume && <div style={{ color: 'var(--wx-red)' }}>上传简历</div>}
                {completed && <div style={{ color: 'var(--wx-green)' }}>个人信息已完善</div>}
                {hasResume && <div style={{ color: 'var(--wx-green)' }}>简历已上传</div>}
              </div>
            </div>
            <button className="btn btn-weak btn-sm" style={{ margin: '10px auto 0' }} onClick={tryViewFull}>去补充信息</button>
          </div>
        )}

        <div className="ai-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/seeker/match/' + job.id)}>
          <div className="ai-card-hd">AI 人岗匹配分析</div>
          <div className="ai-card-bd row between"><span>查看你与该岗位的匹配度</span><span style={{ color: 'var(--wx-text-2)' }}>查看详情</span></div>
        </div>
      </div>

      <div className="page-foot">
        <button className={`btn ${favoriteBusy ? 'btn-disabled' : 'btn-default'}`} style={{ flex: '0 0 48px', padding: 0 }} onClick={toggleFavorite}>{fav ? '★' : '☆'}</button>
        <button className="btn btn-default" style={{ flex: '0 0 48px', padding: 0 }} onClick={() => setShowShare(true)}>分享</button>
        <button className="btn btn-default" style={{ flex: '0 0 92px' }} onClick={startConversation}>留言咨询</button>
        <button
          className="btn btn-primary"
          onClick={() => {
            if (applied) {
              toast('你已经投递过这个岗位')
              return
            }
            if (!unlocked) {
              toast('请先完善个人信息并上传简历')
              tryViewFull()
              return
            }
            navigate('/seeker/apply/' + job.id)
          }}
        >
          投递简历
        </button>
      </div>
    </>
  )
}

export function SeekerProfileEdit() {
  const navigate = useNavigate()
  const toast = useToast()
  const { hasResume, profile, saveProfile } = useProfile()
  const [saving, setSaving] = useState(false)
  const [standardPositions, setStandardPositions] = useState([])
  const [standardPositionLoading, setStandardPositionLoading] = useState(false)
  const [tagOptions, setTagOptions] = useState([])
  const [selectedTagIds, setSelectedTagIds] = useState([])
  const [tagOptionsLoading, setTagOptionsLoading] = useState(false)
  const [form, setForm] = useState({
    real_name: '',
    gender: '',
    education: '',
    experience_years: '',
    standard_position_id: '',
    target_position: '',
    expected_salary: '',
    city: '',
    email: '',
    wechat: '',
  })
  const [pub, setPub] = useState({ name: true, phone: true, email: false, wechat: false, edu: true, exp: false })

  useEffect(() => {
    if (!profile) return
    setForm({
      real_name: profile.real_name || '',
      gender: profile.gender || '',
      education: profile.education || '',
      experience_years: profile.experience_years ?? '',
      standard_position_id: profile.standard_position_id ? String(profile.standard_position_id) : '',
      target_position: profile.target_position || '',
      expected_salary: profile.expected_salary || '',
      city: profile.city || '',
      email: profile.email || '',
      wechat: profile.wechat || '',
    })
    setSelectedTagIds((profile.tag_refs || []).map(item => String(item.id)))
    setPub({
      name: profile.name_public ?? true,
      phone: profile.phone_public ?? true,
      email: profile.email_public ?? false,
      wechat: profile.wechat_public ?? false,
      edu: profile.education_public ?? true,
      exp: profile.experience_public ?? false,
    })
  }, [profile])

  useEffect(() => {
    let alive = true
    const loadStandardPositions = async () => {
      try {
        setStandardPositionLoading(true)
        const data = await listPublicStandardPositions({ limit: 100 })
        if (alive) setStandardPositions(Array.isArray(data.items) ? data.items : [])
      } catch {
        if (alive) setStandardPositions([])
      } finally {
        if (alive) setStandardPositionLoading(false)
      }
    }
    loadStandardPositions()
    return () => { alive = false }
  }, [])

  useEffect(() => {
    let alive = true
    const loadTagOptions = async () => {
      try {
        setTagOptionsLoading(true)
        const data = await listPublicTagLibraryItems({ limit: 100 })
        if (alive) setTagOptions(Array.isArray(data.items) ? data.items : [])
      } catch {
        if (alive) setTagOptions([])
      } finally {
        if (alive) setTagOptionsLoading(false)
      }
    }
    loadTagOptions()
    return () => { alive = false }
  }, [])

  const update = (key, value) => setForm(f => ({ ...f, [key]: value }))

  const updateStandardPosition = (value) => {
    const matched = standardPositions.find(item => String(item.id) === String(value))
    setForm(f => ({
      ...f,
      standard_position_id: value,
      target_position: matched ? matched.name : f.target_position,
    }))
  }

  const toggleTagOption = (id) => {
    const key = String(id)
    setSelectedTagIds(ids => ids.includes(key) ? ids.filter(item => item !== key) : [...ids, key])
  }

  const submit = async () => {
    setSaving(true)
    try {
      await saveProfile({
        ...form,
        experience_years: form.experience_years === '' ? null : Number(form.experience_years),
        standard_position_id: form.standard_position_id === '' ? null : Number(form.standard_position_id),
        tag_ids: selectedTagIds.map(id => Number(id)),
        name_public: pub.name,
        phone_public: pub.phone,
        email_public: pub.email,
        wechat_public: pub.wechat,
        education_public: pub.edu,
        experience_public: pub.exp,
      })
      toast('已保存', '✓')
      navigate(-1)
    } catch (error) {
      toast(error.message || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <NavBar title="完善信息" right={<HomeNavLink />} />
      <div className="page" style={{ paddingBottom: 90 }}>
        <div className="cell-group-title">基本信息</div>
        <div className="cell-group">
          <FormCell label="姓名" req><input value={form.real_name} onChange={e => update('real_name', e.target.value)} placeholder="请输入姓名" /></FormCell>
          <FormCell label="性别"><input value={form.gender} onChange={e => update('gender', e.target.value)} placeholder="男/女" /></FormCell>
          <FormCell label="学历"><input value={form.education} onChange={e => update('education', e.target.value)} placeholder="本科/大专/硕士" /></FormCell>
          <FormCell label="经验"><input value={form.experience_years} onChange={e => update('experience_years', e.target.value)} placeholder="工作年限" /></FormCell>
          <FormCell label="标准职位">
            <select
              value={form.standard_position_id}
              onChange={e => updateStandardPosition(e.target.value)}
              disabled={standardPositionLoading}
            >
              <option value="">{standardPositionLoading ? '加载中...' : '选择标准职位'}</option>
              {standardPositions.map(item => (
                <option key={item.id} value={item.id}>
                  {item.category ? `${item.category} / ${item.name}` : item.name}
                </option>
              ))}
            </select>
          </FormCell>
          <FormCell label="目标岗位"><input value={form.target_position} onChange={e => update('target_position', e.target.value)} placeholder="如 前端开发" /></FormCell>
          <FormCell label="期望薪资"><input value={form.expected_salary} onChange={e => update('expected_salary', e.target.value)} placeholder="如 20K-30K" /></FormCell>
          <FormCell label="城市"><input value={form.city} onChange={e => update('city', e.target.value)} placeholder="如 深圳" /></FormCell>
          <FormCell label="邮箱"><input value={form.email} onChange={e => update('email', e.target.value)} placeholder="用于交换联系方式" /></FormCell>
          <FormCell label="微信"><input value={form.wechat} onChange={e => update('wechat', e.target.value)} placeholder="用于交换联系方式" /></FormCell>
        </div>

        <div className="cell-group-title">能力标签</div>
        <div className="cell-group">
          <div style={{ padding: 16 }}>
            <div className="tiny muted" style={{ marginBottom: 8 }}>
              {tagOptionsLoading ? '标签加载中...' : '从平台标签库选择，用于岗位搜索和人岗匹配。'}
            </div>
            <div className="tagcloud">
              {tagOptions.map(item => {
                const active = selectedTagIds.includes(String(item.id))
                return (
                  <span
                    key={item.id}
                    className={`tag ${active ? 'tag-green' : 'tag-gray'}`}
                    style={{ fontSize: 13, padding: '5px 12px', cursor: 'pointer' }}
                    onClick={() => toggleTagOption(item.id)}
                  >
                    {item.name}
                  </span>
                )
              })}
            </div>
            {!tagOptionsLoading && tagOptions.length === 0 && (
              <div className="tiny muted">暂无可用标签。</div>
            )}
          </div>
        </div>

        <div className="cell-group-title">公开设置</div>
        <div className="cell-group">
          {Object.entries({ name: '姓名', phone: '手机', email: '邮箱', wechat: '微信', edu: '学历', exp: '经验' }).map(([key, label]) => (
            <div className="cell" key={key}><span className="cell-label">{label}</span><Switch on={pub[key]} onClick={() => setPub(p => ({ ...p, [key]: !p[key] }))} /></div>
          ))}
        </div>

        <ResumeUploadInline hasResume={hasResume} />
      </div>
      <div className="page-foot"><button className={`btn ${saving ? 'btn-disabled' : 'btn-primary'}`} onClick={submit}>{saving ? '保存中...' : '保存'}</button></div>
    </>
  )
}

function ResumeUploadInline({ hasResume, onParsed }) {
  const toast = useToast()
  const fileRef = useRef(null)
  const [uploading, setUploading] = useState(false)

  const startUpload = () => fileRef.current?.click()

  const onFileChange = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file || uploading) return
    setUploading(true)
    try {
      const data = await uploadResume(file)
      const parseRunId = data.parse_run?.id || data.current_parse_run_id
      if (parseRunId) {
        try {
          const structured = await getStructuredResult(parseRunId)
          onParsed?.(normalizeStructuredBasic(structured.basic || structured.basic_info))
        } catch {
          // Upload success is enough for this inline widget.
        }
      }
      toast('简历已上传', '✓')
    } catch (error) {
      toast(error.message || '简历上传失败')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="cell-group" style={{ marginTop: 10 }}>
      <input ref={fileRef} type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.webp,.bmp" style={{ display: 'none' }} onChange={onFileChange} />
      <div className="cell link" onClick={startUpload}>
        <span className="cell-label">简历</span>
        <span className="cell-value">{uploading ? '上传中...' : hasResume ? '重新上传' : '点击上传'}</span>
      </div>
    </div>
  )
}

function normalizeStructuredBasic(basic) {
  if (!basic) return null
  const extractValue = (field) => {
    if (!field) return null
    if (typeof field === 'object' && 'value' in field) return field.value
    return field
  }
  return {
    real_name: extractValue(basic.real_name) || extractValue(basic.name) || null,
    gender: extractValue(basic.gender) || null,
    age: extractValue(basic.age) ?? null,
  }
}

export function SeekerChat() {
  return <RealSeekerChat />
}
