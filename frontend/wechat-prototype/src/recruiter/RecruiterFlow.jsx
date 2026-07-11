import React, { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { NavBar, AIBadge, AIButton, AICard, useToast, Sheet, EmotionTag, Switch } from '../components/ui.jsx'
import { aiMock, batchParsedJobs, companyProfile, getRecruiterChat, pickColor } from '../mock/data.js'
import {
  createJob,
  listPublicStandardPositions,
  listPublicTagLibraryItems,
  parseJobDescription,
  parseJobDescriptionText,
  preReviewJobContent,
  suggestJobSalary,
} from '../services/index.js'

/* ============ 发布岗位（AI 代写 / 薪资建议 / 润色） ============ */
export function RecruiterJobCreate() {
  const navigate = useNavigate()
  const toast = useToast()
  const [name, setName] = useState('')
  const [nameTip, setNameTip] = useState('')
  const [standardPositionId, setStandardPositionId] = useState('')
  const [standardPositions, setStandardPositions] = useState([])
  const [standardPositionLoading, setStandardPositionLoading] = useState(false)
  const [city, setCity] = useState('')
  const [salaryLow, setSalaryLow] = useState('')
  const [salaryHigh, setSalaryHigh] = useState('')
  const [showSalaryAI, setShowSalaryAI] = useState(false)
  const [salarySuggestion, setSalarySuggestion] = useState(null)
  const [salarySuggesting, setSalarySuggesting] = useState(false)
  const [duty, setDuty] = useState('')
  const [require, setRequire] = useState('')
  const [writing, setWriting] = useState(false)
  const [tags, setTags] = useState([])
  const [tagOptions, setTagOptions] = useState([])
  const [selectedTagIds, setSelectedTagIds] = useState([])
  const [tagOptionsLoading, setTagOptionsLoading] = useState(false)
  const [tagging, setTagging] = useState(false)
  const [jdUploading, setJdUploading] = useState(false) // B2: 上传JD文件
  const [jdFileName, setJdFileName] = useState('')
  const [jdParseNote, setJdParseNote] = useState('')
  const [jdFullText, setJdFullText] = useState('')
  const [jdTextParsing, setJdTextParsing] = useState(false)
  const [savingDraft, setSavingDraft] = useState(false)
  const jdFileRef = useRef(null)
  const [jdPortraitContext, setJdPortraitContext] = useState(false) // B3: 是否展示了画像上下文
  const [genPortrait, setGenPortrait] = useState(false) // B4: 提交时生成岗位画像过渡

  useEffect(() => {
    let cancelled = false
    const loadStandardPositionOptions = async () => {
      try {
        setStandardPositionLoading(true)
        const data = await listPublicStandardPositions({ limit: 100 })
        if (!cancelled) setStandardPositions(Array.isArray(data.items) ? data.items : [])
      } catch {
        if (!cancelled) setStandardPositions([])
      } finally {
        if (!cancelled) setStandardPositionLoading(false)
      }
    }
    loadStandardPositionOptions()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    const loadTagOptions = async () => {
      try {
        setTagOptionsLoading(true)
        const data = await listPublicTagLibraryItems({ limit: 100 })
        if (!cancelled) setTagOptions(Array.isArray(data.items) ? data.items : [])
      } catch {
        if (!cancelled) setTagOptions([])
      } finally {
        if (!cancelled) setTagOptionsLoading(false)
      }
    }
    loadTagOptions()
    return () => {
      cancelled = true
    }
  }, [])

  const inferJobTags = () => {
    const text = `${name} ${city} ${duty} ${require}`.toLowerCase()
    const rules = [
      ['后端开发', ['后端', '服务端', '接口开发', 'api', 'server']],
      ['Python', ['python']],
      ['FastAPI', ['fastapi']],
      ['Java', ['java', 'spring']],
      ['Spring Boot', ['spring boot', 'springboot']],
      ['数据库', ['数据库', 'postgresql', 'mysql', 'sql', '数据建模']],
      ['接口鉴权', ['jwt', '鉴权', '权限', 'rbac']],
      ['服务稳定性', ['稳定性', '高并发', '性能优化']],
      ['前端开发', ['前端', '页面开发', '小程序']],
      ['React', ['react']],
      ['Vue', ['vue']],
      ['TypeScript', ['typescript', 'ts']],
      ['JavaScript', ['javascript', 'js']],
      ['产品经理', ['产品经理', '需求分析', '产品原型']],
      ['运营', ['运营', '用户增长']],
      ['销售', ['销售', '客户开发']],
      ['本科', ['本科']],
      ['3-5年', ['3-5年', '3 年', '5 年']],
      ['1-3年', ['1-3年', '1 年']],
    ]
    const inferred = []
    for (const [tag, keywords] of rules) {
      if (keywords.some(keyword => text.includes(keyword.toLowerCase())) && !inferred.includes(tag)) {
        inferred.push(tag)
      }
    }
    if (city && !inferred.includes(city)) inferred.push(city)
    return inferred.slice(0, 10)
  }

  const genTags = () => {
    if (!name.trim() && !duty.trim() && !require.trim()) {
      toast('请先填写或解析 JD 内容')
      return
    }
    setTagging(true)
    setTimeout(() => {
      const inferred = inferJobTags()
      const matchedIds = tagOptions
        .filter(item => inferred.includes(item.name) || inferred.includes(item.category))
        .map(item => String(item.id))
      if (matchedIds.length) {
        applySelectedTagIds(matchedIds)
      } else {
        setTags(inferred.length ? inferred : [])
      }
      setTagging(false)
      toast(matchedIds.length ? '已匹配标签库标签' : '未命中标签库，可手动选择标签', '✓')
    }, 600)
  }

  const onNameChange = (v) => {
    setName(v)
    // AI 岗位名称标准化提示
    if (v === '程序员') setNameTip('软件开发工程师')
    else if (v === '美工') setNameTip('UI设计师')
    else if (v === '销售') setNameTip('销售经理')
    else setNameTip('')
  }

  const handleNameInput = (value) => {
    onNameChange(value)
    if (!value.trim() && standardPositionId) setStandardPositionId('')
  }

  const onStandardPositionChange = (value) => {
    setStandardPositionId(value)
    const matched = standardPositions.find(item => String(item.id) === String(value))
    if (matched) {
      setName(matched.name)
      setNameTip('')
    }
  }

  const applySelectedTagIds = (ids) => {
    const uniqueIds = Array.from(new Set(ids.map(item => String(item)).filter(Boolean)))
    setSelectedTagIds(uniqueIds)
    const selectedNames = tagOptions
      .filter(item => uniqueIds.includes(String(item.id)))
      .map(item => item.name)
    setTags(selectedNames)
  }

  const toggleTagOption = (id) => {
    const key = String(id)
    applySelectedTagIds(selectedTagIds.includes(key)
      ? selectedTagIds.filter(item => item !== key)
      : [...selectedTagIds, key])
  }

  const writeJD = () => {
    if (!name) { toast('请先填写岗位名称'); return }
    setWriting(true)
    setJdPortraitContext(true) // B3: 标记使用企业画像
    setTimeout(() => {
      setDuty(aiMock.jdDuty)
      setRequire(aiMock.jdRequire)
      setWriting(false)
      toast('AI 已基于企业画像生成 JD', '✓')
    }, 1500)
  }

  const applyParsedJD = (data) => {
    if (data.title) setName(data.title)
    if (data.city) setCity(data.city)
    if (data.salary_min) setSalaryLow(String(data.salary_min))
    if (data.salary_max) setSalaryHigh(String(data.salary_max))
    if (data.description) setDuty(data.description)
    if (data.requirement) setRequire(data.requirement)
    if (Array.isArray(data.tags) && data.tags.length) setTags(data.tags)

    const missing = Array.isArray(data.missing_fields) ? data.missing_fields : []
    setJdParseNote(missing.length ? `已解析，仍需补充：${missing.join('、')}` : '已解析并回填主要字段')
    setJdPortraitContext(true)
  }

  // B2: 上传JD文件
  const uploadJD = () => {
    if (!jdUploading) jdFileRef.current?.click()
  }

  const handleJDFileChange = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setJdUploading(true)
    setJdFileName(file.name)
    setJdParseNote('')
    try {
      const data = await parseJobDescription(file)
      applyParsedJD(data)
      toast('JD 文件解析完成，内容已回填', '✓')
    } catch (error) {
      setJdParseNote(error.message || 'JD 文件解析失败')
      toast(error.message || 'JD 文件解析失败')
    } finally {
      setJdUploading(false)
    }
  }

  const parseFullJDText = async () => {
    const text = jdFullText.trim()
    if (text.length < 10) {
      toast('请先粘贴完整 JD 文本')
      return
    }
    setJdTextParsing(true)
    setJdFileName('')
    setJdParseNote('')
    try {
      const data = await parseJobDescriptionText(text)
      applyParsedJD(data)
      toast('整段 JD 已解析并回填', '✓')
    } catch (error) {
      setJdParseNote(error.message || '整段 JD 解析失败')
      toast(error.message || '整段 JD 解析失败')
    } finally {
      setJdTextParsing(false)
    }
  }

  const loadSalarySuggestion = async () => {
    if (!name.trim()) {
      toast('请先填写岗位名称')
      return
    }
    if (!city.trim()) {
      toast('请先填写工作城市')
      return
    }
    setShowSalaryAI(true)
    setSalarySuggesting(true)
    try {
      const data = await suggestJobSalary({
        title: name.trim(),
        city: city.trim(),
        experience: require.includes('3-5年') || duty.includes('3-5年') ? '3-5年' : '不限',
        education: require.includes('本科') || duty.includes('本科') ? '本科' : '不限',
        tags,
      })
      setSalarySuggestion(data)
    } catch (error) {
      toast(error.message || '薪资建议获取失败')
      setSalarySuggestion(null)
    } finally {
      setSalarySuggesting(false)
    }
  }

  const buildDraft = () => {
    const low = Number.parseInt(salaryLow, 10)
    const high = Number.parseInt(salaryHigh, 10)
    if (!name.trim()) { toast('请先填写岗位名称'); return null }
    if (!city.trim()) { toast('请先填写工作城市'); return null }
    if (!Number.isFinite(low) || !Number.isFinite(high) || low <= 0 || high < low) {
      toast('请填写正确的月薪范围')
      return null
    }
    if (duty.trim().length < 10) { toast('请填写至少 10 个字的工作职责'); return null }
    if (require.trim().length < 10) { toast('请填写至少 10 个字的任职要求'); return null }

    return {
      standard_position_id: standardPositionId ? Number(standardPositionId) : undefined,
      title: name.trim(),
      city: city.trim(),
      salary_min: low,
      salary_max: high,
      experience: '不限',
      education: '不限',
      description: duty.trim(),
      requirement: require.trim(),
      benefits: null,
      tags,
      tag_ids: selectedTagIds.map(id => Number(id)),
    }
  }

  const saveDraft = async () => {
    const draft = buildDraft()
    if (!draft || savingDraft) return
    try {
      setSavingDraft(true)
      await createJob({ ...draft, status: 'draft' })
      toast('已保存草稿', '✓')
      setTimeout(() => navigate('/recruiter/jobs'), 600)
    } catch (error) {
      toast(error.message || '保存草稿失败')
    } finally {
      setSavingDraft(false)
    }
  }

  return (
    <>
      <NavBar title="发布岗位" />
      <div className="page" style={{ paddingBottom: 90 }}>
        {/* 岗位名称 */}
        <div className="cell-group-title">岗位信息</div>
        <div className="cell-group">
          <div className="form-cell">
            <span className="fc-label">标准职位</span>
            <div className="fc-body">
              <select value={standardPositionId} onChange={e => onStandardPositionChange(e.target.value)}>
                <option value="">{standardPositionLoading ? '加载中...' : '选择标准职位'}</option>
                {standardPositions.map(item => (
                  <option key={item.id} value={item.id}>{item.name}{item.category ? ` / ${item.category}` : ''}</option>
                ))}
              </select>
              <div className="tiny muted" style={{ marginTop: 6 }}>
                选择后自动回填岗位名称，并建立与标准职位库的关联。
              </div>
            </div>
          </div>
          <div className="form-cell">
            <span className="fc-label req">岗位名称</span>
            <div className="fc-body">
              <input value={name} placeholder="如：前端开发工程师" onChange={e => handleNameInput(e.target.value)} />
              {nameTip && (
                <div className="row gap6" style={{ marginTop: 6 }} onClick={() => { setName(nameTip); setNameTip('') }}>
                  <AIBadge soft>AI标准化</AIBadge>
                  <span className="tiny" style={{ color: 'var(--wx-green-dark)' }}>建议使用标准名称「{nameTip}」，点击采纳</span>
                </div>
              )}
            </div>
          </div>
          <div className="form-cell">
            <span className="fc-label req">工作城市</span>
            <div className="fc-body"><input value={city} placeholder="可多选，最多10个" onChange={e => setCity(e.target.value)} /></div>
          </div>
        </div>

        <div className="cell-group-title row between" style={{ paddingRight: 16 }}>
          <span>整段 JD</span>
          <button className={`btn btn-weak btn-sm ${jdTextParsing ? 'btn-disabled' : ''}`} onClick={parseFullJDText} disabled={jdTextParsing}>
            {jdTextParsing ? <><span className="spin" style={{ width: 12, height: 12 }} /> 解析中</> : '解析并填充'}
          </button>
        </div>
        <div className="cell-group">
          <div style={{ padding: '12px 16px' }}>
            <textarea
              value={jdFullText}
              placeholder="可把完整 JD 粘贴到这里，点击「解析并填充」后自动回填岗位名称、城市、薪资、职责和要求"
              onChange={e => setJdFullText(e.target.value)}
              style={{ width: '100%', minHeight: 118, fontSize: 14, lineHeight: 1.7, resize: 'vertical' }}
            />
            <div className="tiny muted" style={{ marginTop: 6 }}>
              适合从微信、文档、招聘网站复制整段 JD；解析后仍可继续手动修改各字段。
            </div>
          </div>
        </div>

        {/* 薪资 + AI 建议 */}
        <div className="cell-group-title">薪资待遇</div>
        <div className="cell-group">
          <div className="form-cell">
            <span className="fc-label req">月薪范围</span>
            <div className="fc-body">
              <div className="row gap8">
                <input style={{ width: 70 }} value={salaryLow} placeholder="最低K" onChange={e => setSalaryLow(e.target.value)} />
                <span className="muted">-</span>
                <input style={{ width: 70 }} value={salaryHigh} placeholder="最高K" onChange={e => setSalaryHigh(e.target.value)} />
                <span className="grow" />
                <AIButton onClick={loadSalarySuggestion} loading={salarySuggesting}>{salarySuggesting ? '估算中' : '薪资建议'}</AIButton>
              </div>
            </div>
          </div>
        </div>
        {showSalaryAI && (
          <AICard title="AI 薪资建议" tip="基于岗位名称、城市、经验、学历和标签的规则估算，仅供参考">
            {salarySuggesting && <div className="tiny muted">正在估算薪资区间...</div>}
            {!salarySuggesting && salarySuggestion && (<>
              该岗位在{city || '当前城市'}的建议薪资区间约为 <b>{salarySuggestion.salary_min}K - {salarySuggestion.salary_max}K</b>／月。
              <div style={{ marginTop: 6, padding: '6px 8px', background: '#FFF', borderRadius: 6, lineHeight: 1.7 }}>
                <div className="tiny">📊 同类岗位市场中位值：<b style={{ color: 'var(--wx-green-dark)' }}>{salarySuggestion.market_median}K</b></div>
                <div className="tiny">🏢 对标企业中位薪资：<b style={{ color: 'var(--wx-blue)' }}>{salarySuggestion.benchmark_median}K</b></div>
                <div className="tiny">置信度：<b>{Math.round((salarySuggestion.confidence || 0) * 100)}%</b></div>
                <div className="tiny muted" style={{ marginTop: 2 }}>
                  对标参考：{(salarySuggestion.benchmark_companies || []).join(' / ')}
                </div>
                <div className="tiny muted" style={{ marginTop: 2 }}>
                  估算依据：{salarySuggestion.basis}
                </div>
                {(salarySuggestion.factors || []).length > 0 && (
                  <div className="tagcloud" style={{ marginTop: 6 }}>
                    {salarySuggestion.factors.map(f => <span key={f} className="tag tag-gray">{f}</span>)}
                  </div>
                )}
              </div>
              <div style={{ marginTop: 8 }}>
                <button className="btn btn-weak btn-sm" onClick={() => { setSalaryLow(String(salarySuggestion.salary_min)); setSalaryHigh(String(salarySuggestion.salary_max)); setShowSalaryAI(false); toast('已采用 AI 建议') }}>采用此区间</button>
              </div>
            </>)}
            {!salarySuggesting && !salarySuggestion && <div className="tiny muted">暂未获取到薪资建议，请补充岗位名称和城市后重试。</div>}
          </AICard>
        )}

        {/* 工作职责 + AI 代写 + 上传JD */}
        <div className="cell-group-title row between" style={{ paddingRight: 16 }}>
          <span>工作职责</span>
          <div className="row gap6">
            <input
              ref={jdFileRef}
              type="file"
              accept=".txt,.md,.csv,.docx,.xlsx,.pdf,.jpg,.jpeg,.png,.webp,.bmp,.heic,.heif,image/*,application/pdf"
              style={{ display: 'none' }}
              onChange={handleJDFileChange}
            />
            <button className="btn btn-weak btn-sm" onClick={uploadJD} disabled={jdUploading}>
              {jdUploading ? <><span className="spin" style={{ width: 12, height: 12 }} /> 解析中</> : '📄 上传JD'}
            </button>
            <AIButton onClick={writeJD} loading={writing}>{writing ? 'AI 生成中…' : 'AI 一键代写'}</AIButton>
          </div>
        </div>
        <div className="ai-tip padx" style={{ paddingTop: 4, paddingBottom: 0 }}>
          可直接粘贴文本，也可上传 PDF / Word / Excel / 图片解析后回填；复制文本不会额外解析。
          {jdFileName && <span> 当前文件：{jdFileName}</span>}
          {jdParseNote && <div style={{ marginTop: 4 }}>{jdParseNote}</div>}
        </div>
        {/* B3: 企业画像输入上下文提示 */}
        {jdPortraitContext && (
          <div className="ai-tip padx" style={{ paddingTop: 4, paddingBottom: 0 }}>
            ⚡ AI 基于企业画像（{companyProfile.oneline.slice(0, 40)}…）为你生成 JD，使岗位描述更能体现企业特色
          </div>
        )}
        <div className="cell-group">
          <div style={{ padding: '12px 16px' }}>
            {duty && <div className="row gap6" style={{ marginBottom: 6 }}><AIBadge>AI生成</AIBadge><span className="tiny muted">请根据实际情况修改</span></div>}
            <textarea value={duty} placeholder="填写工作职责，或点击右上「AI 一键代写」" onChange={e => setDuty(e.target.value)}
              style={{ width: '100%', minHeight: 100, fontSize: 14, lineHeight: 1.7, resize: 'none' }} />
          </div>
        </div>

        {/* 任职要求 */}
        <div className="cell-group-title">任职要求</div>
        <div className="cell-group">
          <div style={{ padding: '12px 16px' }}>
            {require && <div className="row gap6" style={{ marginBottom: 6 }}><AIBadge>AI生成</AIBadge><span className="tiny muted">请根据实际情况修改</span></div>}
            <textarea value={require} placeholder="填写任职要求" onChange={e => setRequire(e.target.value)}
              style={{ width: '100%', minHeight: 90, fontSize: 14, lineHeight: 1.7, resize: 'none' }} />
          </div>
        </div>

        {/* 岗位标签 */}
        <div className="cell-group-title row between" style={{ paddingRight: 16 }}>
          <span>岗位标签</span>
          <AIButton onClick={genTags} loading={tagging}>{tagging ? '生成中…' : 'AI 智能打标'}</AIButton>
        </div>
        <div className="cell-group"><div style={{ padding: 16 }}>
          <div className="tiny muted" style={{ marginBottom: 8 }}>
            {tagOptionsLoading ? '标签加载中...' : '从后台标签库选择，提交后保存统一标签 ID。AI 打标会优先匹配标签库。'}
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
            <div className="tiny muted">暂无可用标签，请先在后台标签库维护。</div>
          )}
          {tags.length > 0 && (
            <div className="row gap6" style={{ marginTop: 10 }}>
              <AIBadge soft>已选</AIBadge>
              <span className="tiny muted">{tags.join('、')}</span>
            </div>
          )}
        </div></div>

        <div className="ai-tip padx" style={{ marginTop: 10, lineHeight: 1.7 }}>
          岗位提交后将进入平台审核，审核通过后才会对求职者可见。请确保职位信息真实、完整、合法；审核结果会在我的岗位中展示。
        </div>
      </div>

      <div className="page-foot">
        <button className={`btn btn-default ${savingDraft ? 'btn-disabled' : ''}`} style={{ flex: '0 0 100px' }} disabled={savingDraft} onClick={saveDraft}>
          {savingDraft ? '保存中...' : '存草稿'}
        </button>
        <button className="btn btn-primary" onClick={() => {
          const draft = buildDraft()
          if (!draft) return
          setGenPortrait(true)
          setTimeout(() => { setGenPortrait(false); navigate('/recruiter/job/review', { state: { jobDraft: draft } }) }, 1500)
        }}>
          {genPortrait ? <><span className="spin" style={{ width: 14, height: 14 }} /> AI 生成画像中…</> : '提交发布'}
        </button>
      </div>
      {/* B4: 画像生成过渡提示 */}
      {genPortrait && (
        <div className="ai-tip center" style={{ position: 'fixed', bottom: 80, left: 0, right: 0, zIndex: 10, margin: '0 16px', background: 'var(--ai-bg)', padding: '12px', borderRadius: 8 }}>
          ⚡ AI 正在基于岗位信息自动生成岗位画像（标签+维度评分），提交后将可在「岗位画像」页查看
        </div>
      )}
    </>
  )
}

function runJobContentReview(jobDraft) {
  if (!jobDraft) {
    return {
      level: 'block',
      title: 'AI 内容预审：拦截',
      summary: '岗位草稿已失效，无法提交审核。',
      findings: [{ label: '草稿缺失', suggestion: '请返回发布页重新填写岗位信息。' }],
      cardStyle: { background: '#FFF1F0', borderColor: '#FFCCC7', color: 'var(--wx-red)' },
    }
  }

  const text = [
    jobDraft.title,
    jobDraft.city,
    jobDraft.experience,
    jobDraft.education,
    jobDraft.description,
    jobDraft.requirement,
    jobDraft.benefits,
    ...(jobDraft.tags || []),
  ].filter(Boolean).join('\n')

  const rules = [
    {
      level: 'block',
      label: '歧视性用语',
      patterns: ['仅限男性', '限男性', '男性优先', '仅限女性', '限女性', '女性优先', '不要女生', '不要男生'],
      suggestion: '删除性别限制，改为与岗位能力直接相关的要求。',
    },
    {
      level: 'block',
      label: '年龄限制',
      patterns: ['35岁以下', '30岁以下', '年龄不超过', '限35岁', '限30岁'],
      suggestion: '删除年龄门槛，改为经验、技能、体力或排班等客观要求。',
    },
    {
      level: 'warning',
      label: '夸大承诺',
      patterns: ['轻松月入', '稳赚', '保底年薪百万', '躺赚', '无需经验月入'],
      suggestion: '避免无法验证的收益承诺，使用明确薪资范围和绩效规则。',
    },
    {
      level: 'warning',
      label: '外部联系方式',
      patterns: ['微信', '加v', '加 V', 'QQ', '电话联系', '手机号'],
      suggestion: '建议使用平台内沟通或企业公开邮箱，避免绕开平台对接流程。',
    },
  ]

  const findings = []
  for (const rule of rules) {
    const hit = rule.patterns.find(pattern => text.includes(pattern))
    if (hit) findings.push({ ...rule, hit })
  }

  if ((jobDraft.description || '').trim().length < 30) {
    findings.push({
      level: 'warning',
      label: '职责描述偏短',
      hit: '工作职责',
      suggestion: '补充 3-5 条具体工作内容，便于求职者判断匹配度。',
    })
  }
  if ((jobDraft.requirement || '').trim().length < 30) {
    findings.push({
      level: 'warning',
      label: '任职要求偏短',
      hit: '任职要求',
      suggestion: '补充技能、经验、协作方式等客观要求。',
    })
  }

  const hasBlock = findings.some(item => item.level === 'block')
  const hasWarning = findings.some(item => item.level === 'warning')
  if (hasBlock) {
    return {
      level: 'block',
      title: 'AI 内容预审：拦截',
      summary: '检测到严重违规风险，需修改后再提交人工审核。',
      findings,
      cardStyle: { background: '#FFF1F0', borderColor: '#FFCCC7', color: 'var(--wx-red)' },
    }
  }
  if (hasWarning) {
    return {
      level: 'warning',
      title: 'AI 内容预审：警告',
      summary: '检测到可优化项，不阻断提交，但会随岗位进入人工审核记录。',
      findings,
      cardStyle: { background: '#FFF7E6', borderColor: '#FFE0A6', color: '#D9941A' },
    }
  }
  return {
    level: 'pass',
    title: 'AI 内容预审：通过',
    summary: '未检测到明显违规风险，岗位将进入平台审核队列。',
    findings: [],
    cardStyle: { background: '#ECF9F1', borderColor: '#BFE8CD', color: 'var(--wx-green-dark)' },
  }
}

function normalizeJobContentReview(result, jobDraft) {
  if (!result) return runJobContentReview(jobDraft)
  const level = result.level || 'warning'
  const cardStyle = level === 'block'
    ? { background: '#FFF1F0', borderColor: '#FFCCC7', color: 'var(--wx-red)' }
    : level === 'warning'
      ? { background: '#FFF7E6', borderColor: '#FFE0A6', color: '#D9941A' }
      : { background: '#ECF9F1', borderColor: '#BFE8CD', color: 'var(--wx-green-dark)' }
  const titleMap = {
    pass: 'AI 内容预审：通过',
    warning: 'AI 内容预审：警告',
    block: 'AI 内容预审：拦截',
  }
  return {
    level,
    title: titleMap[level] || 'AI 内容预审',
    summary: result.summary || '岗位内容预审完成。',
    findings: (result.findings || []).map(item => ({
      level: item.severity,
      label: item.category,
      hit: item.evidence,
      suggestion: item.suggestion,
    })),
    cardStyle,
    promptVersion: result.prompt_version,
    promptSource: result.prompt_source,
  }
}

/* ============ 发布审核（AI 内容预审三级） ============ */
export function RecruiterJobReview() {
  const navigate = useNavigate()
  const location = useLocation()
  const toast = useToast()
  const [submitting, setSubmitting] = useState(false)
  const jobDraft = location.state?.jobDraft
  const [visibility, setVisibility] = useState({
    company_display_mode: 'company_name',
    contact_phone_public: false,
    contact_email_public: true,
    contact_wechat_public: false,
  })
  const [review, setReview] = useState(() => runJobContentReview(jobDraft))
  const [stage, setStage] = useState('checking') // checking | result
  const setVisibilityField = (key, value) => setVisibility(current => ({ ...current, [key]: value }))
  React.useEffect(() => {
    let cancelled = false
    const runReview = async () => {
      try {
        if (!jobDraft) {
          setReview(runJobContentReview(jobDraft))
          return
        }
        const result = await preReviewJobContent(jobDraft)
        if (!cancelled) setReview(normalizeJobContentReview(result, jobDraft))
      } catch (error) {
        if (!cancelled) {
          setReview(runJobContentReview(jobDraft))
          toast(error.message || 'AI 预审接口失败，已使用本地规则兜底')
        }
      } finally {
        if (!cancelled) setStage('result')
      }
    }
    const t = setTimeout(runReview, 600)
    return () => {
      cancelled = true
      clearTimeout(t)
    }
  }, [jobDraft, toast])

  return (
    <>
      <NavBar title="发布审核" />
      <div className="page" style={{ paddingBottom: 90 }}>
        {stage === 'checking' && (
          <div className="empty" style={{ paddingTop: 100 }}>
            <span className="spin" style={{ width: 30, height: 30 }} />
            <div style={{ marginTop: 16 }}>AI 正在预审岗位内容…</div>
            <div className="tiny muted" style={{ marginTop: 6 }}>检测敏感词 / 歧视性用语 / 虚假信息</div>
          </div>
        )}

        {stage === 'result' && (
          <>
            <div className="ai-card" style={{ background: review.cardStyle.background, borderColor: review.cardStyle.borderColor }}>
              <div className="ai-card-hd" style={{ color: review.cardStyle.color }}>{review.title}</div>
              <div className="ai-card-bd" style={{ color: review.cardStyle.color }}>
                <div>{review.summary}</div>
                {jobDraft?.title && <div style={{ marginTop: 6 }}>岗位：{jobDraft.title}</div>}
                {review.findings.length > 0 && (
                  <div style={{ marginTop: 10 }}>
                    {review.findings.map((item, index) => (
                      <div key={`${item.label}-${index}`} style={{ marginTop: 8, padding: '8px 10px', background: '#FFF', borderRadius: 6, color: '#333' }}>
                        <div><b>{item.label}</b>{item.hit && <>：<span className="hl-warn">「{item.hit}」</span></>}</div>
                        <div className="tiny muted" style={{ marginTop: 4 }}>{item.suggestion}</div>
                      </div>
                    ))}
                  </div>
                )}
                {review.findings.length === 0 && <div className="tiny muted" style={{ marginTop: 8 }}>已完成敏感词、歧视性用语、虚假承诺、联系方式导流和完整性检查。</div>}
              </div>
            </div>

            <div className="cell-group" style={{ marginTop: 10 }}>
              <div style={{ padding: 16 }}>
                <div className="tiny muted" style={{ marginBottom: 8 }}>AI 三级预审说明</div>
                <div className="row gap8" style={{ marginBottom: 6 }}><span className="tag tag-green">通过</span><span className="tiny muted">无问题，直接进入审核队列</span></div>
                <div className="row gap8" style={{ marginBottom: 6 }}><span className="tag tag-orange">警告</span><span className="tiny muted">有可优化项，不阻断、标注提醒（当前）</span></div>
                <div className="row gap8"><span className="tag tag-red">拦截</span><span className="tiny muted">严重违规，必须修改后方可提交</span></div>
              </div>
            </div>

            {/* 公开信息设置 + AI 推荐方案 */}
            <div className="cell-group-title">对外公开信息</div>
            <AICard title="AI 推荐公开方案">
              检测到你是认证企业，建议展示<b>企业真名</b>提升信任度；联系方式优先公开<b>企业邮箱</b>以保护个人隐私。
            </AICard>
            <div className="cell-group">
              <div className="cell">
                <span className="cell-label">企业名称展示</span>
                <select
                  value={visibility.company_display_mode}
                  onChange={event => setVisibilityField('company_display_mode', event.target.value)}
                  style={{ border: 0, background: 'transparent', textAlign: 'right', color: 'var(--wx-text-2)', fontSize: 14 }}
                >
                  <option value="company_name">企业真名</option>
                  <option value="display_name">招聘者昵称</option>
                  <option value="anonymous">匿名企业</option>
                </select>
              </div>
              {[
                ['contact_email_public', '企业邮箱'],
                ['contact_phone_public', '联系电话'],
                ['contact_wechat_public', '微信'],
              ].map(([key, label]) => (
                <div className="cell" key={key}>
                  <span className="cell-label">{label}</span>
                  <Switch on={visibility[key]} onClick={() => setVisibilityField(key, !visibility[key])} />
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {stage === 'result' && (
        <div className="page-foot">
          <button className="btn btn-default" style={{ flex: '0 0 110px' }} onClick={() => navigate(-1)}>去修改</button>
          <button className={`btn ${submitting ? 'btn-disabled' : 'btn-primary'}`} disabled={submitting} onClick={async () => {
            if (!jobDraft) {
              toast('岗位草稿已失效，请返回重新提交')
              navigate('/recruiter/job/create')
              return
            }
            if (review.level === 'block') {
              toast('请先修改拦截项后再提交')
              return
            }
            try {
              setSubmitting(true)
              await createJob({ ...jobDraft, ...visibility, status: 'pending' })
              toast('已提交审核，审核通过后对求职者可见', '✓')
              setTimeout(() => navigate('/recruiter/jobs'), 900)
            } catch (error) {
              toast(error.message || '提交审核失败')
            } finally {
              setSubmitting(false)
            }
          }}>{submitting ? '提交中...' : '直接提交审核'}</button>
        </div>
      )}
    </>
  )
}

/* ============ 招聘者对话（AI 智能回复 + 交换联系方式 BR-X-001） ============ */
export function RecruiterChat() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const chat = getRecruiterChat(id) || getRecruiterChat('1')
  const [msgs, setMsgs] = useState(chat.messages)
  const [input, setInput] = useState('')
  const [showAI, setShowAI] = useState(false)
  const [exchanged, setExchanged] = useState(false)

  const send = (text) => {
    if (!text.trim()) return
    setMsgs(m => [...m, { from: 'me', text, time: '刚刚' }])
    setInput(''); setShowAI(false)
  }

  return (
    <>
      <NavBar title={`${chat.name}${chat.virtual ? '（虚拟名）' : ''}`} right={<span onClick={() => navigate('/recruiter/talent/' + chat.id)}>查看简历 ›</span>} />
      <div className="page chat-page" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="grow" style={{ overflowY: 'auto', paddingBottom: 8 }}>
          <div className="ai-tip center" style={{ padding: '10px 0' }}>该应聘者应聘「{chat.job}」 · <EmotionTag level={chat.emotion} /></div>
          {msgs.map((m, i) => (
            <div key={i} className={`msg ${m.from}`}>
              {m.from === 'them' && <span className="avatar" style={{ background: pickColor(chat.logoIdx) }}>{chat.name[0]}</span>}
              <div>
                <div className="bubble">
                  {m.text}
                  {m.isInterview && <div className="interview-flag">📅 疑似面试邀约</div>}
                </div>
              </div>
            </div>
          ))}
          {exchanged && (
            <div style={{ margin: '12px 16px', padding: '14px', background: 'linear-gradient(135deg,#ECF9F1,#FFF7E6)', borderRadius: 10, textAlign: 'center' }}>
              <div style={{ fontSize: 28, marginBottom: 6 }}>🤝</div>
              <div style={{ fontWeight: 600, color: 'var(--wx-green-dark)', fontSize: 14 }}>对接成功！</div>
              <div className="tiny muted" style={{ marginTop: 4, lineHeight: 1.6 }}>
                对方手机：138****6677<br />
                对方邮箱：liran****@mail.com<br />
                可通过以上方式联系候选人，约定面试时间
              </div>
            </div>
          )}
        </div>

        {/* AI 智能回复建议 */}
        {showAI && (
          <div className="ai-suggests">
            <div className="as-hd">⚡ AI 建议回复（点击使用）</div>
            {aiMock.recruiterReplies.map((r, i) => (
              <div key={i} className="as-item" onClick={() => send(r.text)}>
                <span className="as-style">{r.style}</span>{r.text}
              </div>
            ))}
          </div>
        )}

        {/* 输入栏 */}
        <div className="chat-bar">
          <div className="row gap8" style={{ marginBottom: 8 }}>
            <button className="ai-btn" onClick={() => setShowAI(s => !s)}>⚡ AI 回复</button>
            <button className="ai-btn" style={{ color: 'var(--wx-orange)', borderColor: '#FFE0A6', background: '#FFF7E6' }} onClick={() => toast('测评链接已发送给' + chat.name, '📋')}>📋 推送测评</button>
            {!exchanged && <button className="ai-btn" style={{ color: 'var(--wx-blue)', borderColor: '#BEE3FA', background: '#EFF8FF' }} onClick={() => { setExchanged(true); toast('对方已确认，联系方式已互换', '🤝') }}>🤝 请求交换联系方式</button>}
          </div>
          <div className="cb-input-row">
            <div className="cb-input" contentEditable suppressContentEditableWarning
              onInput={e => setInput(e.currentTarget.textContent)}
              style={{ minHeight: 20 }} />
            <button className="cb-send" onClick={() => send(input)}>发送</button>
          </div>
        </div>
      </div>
    </>
  )
}

/* ============ 批量导入岗位（上传 Excel → AI 解析 → 多条预览 → 批量提交） ============ */
export function RecruiterJobUpload() {
  const navigate = useNavigate()
  const toast = useToast()
  const [stage, setStage] = useState('idle') // idle | parsing | done
  const [rows, setRows] = useState([])
  const [picked, setPicked] = useState(new Set())

  const upload = () => {
    setStage('parsing')
    setTimeout(() => {
      setRows(batchParsedJobs)
      setPicked(new Set(batchParsedJobs.filter(r => r.valid).map(r => r.id)))
      setStage('done')
      toast('AI 解析完成', '✓')
    }, 1800)
  }
  const toggle = (id) => setPicked(p => { const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n })

  return (
    <>
      <NavBar title="批量导入岗位" />
      <div className="page" style={{ paddingBottom: stage === 'done' ? 80 : 90 }}>
        {/* 上传区 */}
        <div className="cell-group-title">上传岗位表格</div>
        <div className="cell-group"><div style={{ padding: 16 }}>
          <div className={`uploader ${stage === 'done' ? 'done' : ''}`} onClick={stage === 'idle' ? upload : undefined}>
            {stage === 'idle' && (<>
              <span style={{ fontSize: 34 }}>📊</span>
              <span style={{ fontSize: 14 }}>上传 Excel / CSV 岗位表</span>
              <AIBadge soft>AI 批量解析</AIBadge>
            </>)}
            {stage === 'parsing' && (<>
              <span className="spin" style={{ width: 24, height: 24 }} />
              <span style={{ fontSize: 14 }}>AI 正在解析表格…</span>
              <span className="tiny muted">识别岗位 / 城市 / 薪资并标准化</span>
            </>)}
            {stage === 'done' && (<>
              <span style={{ fontSize: 30 }}>✅</span>
              <span style={{ fontSize: 14, color: 'var(--wx-green-dark)' }}>共解析出 {rows.length} 条岗位</span>
            </>)}
          </div>
          {stage === 'idle' && <div className="ai-tip" style={{ marginTop: 10 }}>支持模板：岗位名称 / 城市 / 薪资 / 职责 / 要求。点击上方区域选择文件（演示）</div>}
        </div></div>

        {/* 解析结果 */}
        {stage === 'done' && (<>
          <div className="cell-group-title row between" style={{ paddingRight: 16 }}>
            <span>解析结果（勾选要发布的）</span>
            <span className="tiny" style={{ color: 'var(--wx-green-dark)' }}>已选 {picked.size}/{rows.length}</span>
          </div>
          <div className="cell-group">
            {rows.map(r => (
              <div key={r.id} className="cell" style={{ alignItems: 'flex-start' }} onClick={() => r.valid && toggle(r.id)}>
                <span style={{ marginRight: 10, fontSize: 18, color: !r.valid ? 'var(--wx-text-light)' : picked.has(r.id) ? 'var(--wx-green)' : 'var(--wx-text-light)' }}>
                  {!r.valid ? '⚠' : picked.has(r.id) ? '☑' : '☐'}
                </span>
                <div className="grow">
                  <div className="row between">
                    <span style={{ fontWeight: 500 }}>{r.name}</span>
                    <span className="tag tag-orange">{r.salary}</span>
                  </div>
                  <div className="row gap6" style={{ marginTop: 4, flexWrap: 'wrap' }}>
                    <span className="tag tag-gray">{r.city}</span>
                    <span className="ai-badge soft">AI解析</span>
                  </div>
                  {r.warn && <div className="tiny" style={{ color: 'var(--wx-orange)', marginTop: 4 }}>⚠ {r.warn}</div>}
                </div>
              </div>
            ))}
          </div>
          <div className="ai-tip padx">⚠ 标记的岗位信息不完整，需补充后才能发布；其余将批量提交审核。</div>
        </>)}
      </div>

      <div className="page-foot">
        {stage === 'done'
          ? <button className={`btn ${picked.size ? 'btn-primary' : 'btn-disabled'}`} onClick={() => { if (!picked.size) return; toast(`已提交 ${picked.size} 条岗位审核`, '✓'); setTimeout(() => navigate('/recruiter/jobs'), 1000) }}>批量提交 {picked.size} 条岗位</button>
          : <button className={`btn ${stage === 'parsing' ? 'btn-disabled' : 'btn-primary'}`} onClick={stage === 'idle' ? upload : undefined}>{stage === 'parsing' ? '解析中…' : '上传并解析'}</button>}
      </div>
    </>
  )
}
