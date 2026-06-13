import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, AIBadge, AIButton, AICard, FormCell, useToast, Switch } from '../components/ui.jsx'
import { getFeedJob, getSeekerChat, aiMock, pickColor } from '../mock/data.js'
import { ShareSheet } from './SeekerExtra.jsx'
import { useProfile } from '../common/ProfileContext.jsx'
import { listMyApplications } from '../services/index.js'
import { findPublicJobById } from '../utils/jobView.js'

/* ============ 岗位详情（查看完整信息需补充个人信息） ============ */
export function SeekerJobDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const fallbackJob = getFeedJob(id) || getFeedJob('1')
  const [job, setJob] = useState(fallbackJob)
  const [jobError, setJobError] = useState('')
  const [applied, setApplied] = useState(false)
  const { unlocked, completed, hasResume } = useProfile()
  // 如果从补信息页回来且 state 中有 unlocked 标记，使用 context 中的最新状态
  const [fav, setFav] = useState(false)
  const [showShare, setShowShare] = useState(false)

  useEffect(() => {
    let alive = true
    findPublicJobById(id)
      .then(realJob => {
        if (!alive) return
        if (realJob) {
          setJob(realJob)
          setJobError('')
          return
        }
        setJob(fallbackJob)
        setJobError('未找到真实公开岗位，当前显示演示岗位。')
      })
      .catch(error => {
        if (!alive) return
        setJob(fallbackJob)
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

  const tryViewFull = () => {
    navigate('/seeker/profile/edit?from=job&id=' + job.id)
  }

  return (
    <>
      <NavBar title="职位详情" right={<span onClick={() => setShowShare(true)}>⋯</span>} />
      {showShare && <ShareSheet title="分享职位给好友" onClose={() => setShowShare(false)} />}
      <div className="page" style={{ paddingBottom: 80 }}>
        {jobError && <div className="ai-tip padx" style={{ paddingTop: 12, color: 'var(--wx-red)' }}>{jobError}</div>}
        <div style={{ background: '#fff', padding: 16 }}>
          <div className="row between">
            <span style={{ fontSize: 20, fontWeight: 700 }}>{job.name}</span>
            <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--wx-orange)' }}>{job.salary}</span>
          </div>
          <div className="jc-meta" style={{ marginTop: 10 }}>
            <span className="tag tag-gray">{job.city}</span>
            <span className="tag tag-gray">{job.exp}</span>
            <span className="tag tag-gray">{job.edu}</span>
          </div>
          {job.tags.map(t => <span key={t} className="tag tag-green" style={{ marginRight: 6 }}>{t}</span>)}
          <div className="row gap6" style={{ background: 'var(--ai-bg)', borderRadius: 6, padding: '8px 10px', marginTop: 12 }}>
            <AIBadge>AI亮点</AIBadge><span className="tiny" style={{ color: '#3a5a48' }}>{job.aiHighlight}</span>
          </div>
        </div>

        {/* 公司（A1: 可点击查看企业画像） */}
        <div className="cell-group" style={{ marginTop: 10 }}>
          <div className="cell link" onClick={() => navigate('/seeker/company-portrait')}>
            <span className="jc-logo" style={{ marginRight: 10 }}>{job.companyShow[0]}</span>
            <div className="grow"><div style={{ fontWeight: 500 }}>{job.companyShow}</div><div className="tiny muted">{job.virtual ? '该企业使用虚拟名展示' : '已通过企业认证'}<span style={{ color: 'var(--wx-green-dark)', marginLeft: 6 }}>查看画像 ›</span></div></div>
          </div>
        </div>

        {/* 职责 / 要求：未解锁时部分模糊 */}
        <div className="cell-group-title">工作职责</div>
        <div className="cell-group">
          <div style={{ padding: 16, whiteSpace: 'pre-line', lineHeight: 1.8, fontSize: 14, position: 'relative' }}>
            <div style={!unlocked ? { maxHeight: 76, overflow: 'hidden', maskImage: 'linear-gradient(#000 40%, transparent)', WebkitMaskImage: 'linear-gradient(#000 40%, transparent)' } : undefined}>
              {job.duty}
            </div>
          </div>
        </div>
        {unlocked && (<>
          <div className="cell-group-title">任职要求</div>
          <div className="cell-group"><div style={{ padding: 16, whiteSpace: 'pre-line', lineHeight: 1.8, fontSize: 14 }}>{job.require}</div></div>
          <div className="cell-group-title">联系方式</div>
          <div className="cell-group"><div className="cell"><span className="cell-label">联系方式</span><span className="cell-value">{job.contactMethod}</span></div></div>
        </>)}

        {!unlocked && (
          <div className="ai-card center">
            <div className="ai-card-bd">
              🔒 查看完整信息与投递需满足：
              <div style={{ textAlign: 'left', padding: '6px 16px', fontSize: 13, lineHeight: 1.8 }}>
                {!completed && <div style={{ color: 'var(--wx-red)' }}>✗ 完善个人信息（必填项）</div>}
                {!hasResume && <div style={{ color: 'var(--wx-red)' }}>✗ 上传简历</div>}
                {completed && <div style={{ color: 'var(--wx-green)' }}>✓ 个人信息已完善</div>}
                {hasResume && <div style={{ color: 'var(--wx-green)' }}>✓ 简历已上传</div>}
              </div>
            </div>
            <button className="btn btn-weak btn-sm" style={{ margin: '10px auto 0' }} onClick={tryViewFull}>去补充信息</button>
          </div>
        )}

        {/* AI 人岗匹配分析入口 */}
        <div className="ai-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/seeker/match/' + job.id)}>
          <div className="ai-card-hd">⚡ AI 人岗匹配分析</div>
          <div className="ai-card-bd row between">
            <span>你与该岗位匹配度 <b style={{ color: 'var(--wx-green)' }}>{job.matchScore}%</b></span>
            <span style={{ color: 'var(--wx-text-2)' }}>查看详情 ›</span>
          </div>
        </div>
      </div>

      <div className="page-foot">
        <button className="btn btn-default" style={{ flex: '0 0 48px', padding: 0 }} onClick={() => { setFav(f => !f); toast(fav ? '已取消收藏' : '已收藏') }}>{fav ? '★' : '☆'}</button>
        <button className="btn btn-default" style={{ flex: '0 0 48px', padding: 0 }} onClick={() => setShowShare(true)}>↗</button>
        <button className="btn btn-default" style={{ flex: '0 0 92px' }} onClick={() => unlocked ? navigate('/seeker/chat/101') : tryViewFull()}>
          留言咨询
          {!unlocked && <span className="tiny" style={{ display: 'block', color: 'var(--wx-text-light)', fontSize: 10 }}>需先完善信息</span>}
        </button>
        <button className="btn btn-primary" onClick={() => {
          if (applied) { toast('你已经投递过这个岗位'); return }
          if (!unlocked) { toast('请先完善个人信息并上传简历', '🔒'); tryViewFull(); return }
          navigate('/seeker/apply/' + job.id)
        }}>
          投递简历
        </button>
      </div>
    </>
  )
}

/* ============ 补充个人信息（AI 薪资期望建议 + 公开/私密） ============ */
export function SeekerProfileEdit() {
  const navigate = useNavigate()
  const toast = useToast()
  const { completed, hasResume, markCompleted } = useProfile()
  const [salary, setSalary] = useState('')
  const [showSalaryAI, setShowSalaryAI] = useState(false)
  const [pub, setPub] = useState({ name: true, phone: true, edu: true, exp: false })

  return (
    <>
      <NavBar title="完善个人信息" />
      <div className="page" style={{ paddingBottom: 90 }}>
        <div className="ai-tip padx" style={{ paddingTop: 12 }}>⚡ AI 渐进式收集：先填必填项即可查看岗位，其余可稍后补充。每个字段可单独设置是否对招聘者公开。</div>

        <div className="cell-group-title">基本信息（必填）</div>
        <div className="cell-group">
          <PubCell label="姓名" req value="李然（虚拟名）" on={pub.name} onToggle={() => setPub(p => ({ ...p, name: !p.name }))} />
          <FormCell label="性别" req><input placeholder="请选择" /></FormCell>
          <FormCell label="最高学历" req><input placeholder="本科" /></FormCell>
        </div>

        <div className="cell-group-title">联系方式（必填）</div>
        <div className="cell-group">
          <PubCell label="手机号" req value="138****6677" on={pub.phone} onToggle={() => setPub(p => ({ ...p, phone: !p.phone }))} />
        </div>

        <div className="cell-group-title">期望信息（选填）</div>
        <div className="cell-group">
          <div className="form-cell">
            <span className="fc-label">期望薪资</span>
            <div className="fc-body">
              <div className="row gap8">
                <input className="grow" value={salary} placeholder="如 20K-30K" onChange={e => setSalary(e.target.value)} />
                <AIButton onClick={() => setShowSalaryAI(true)}>薪资建议</AIButton>
              </div>
            </div>
          </div>
        </div>
        {showSalaryAI && (
          <AICard title="AI 薪资期望建议" tip="基于「本科+5年经验+深圳」的市场数据分析，仅供参考">
            建议期望薪资区间 <b>22K - 30K</b>／月。
            <div style={{ marginTop: 8 }}><button className="btn btn-weak btn-sm" onClick={() => { setSalary('22K-30K'); setShowSalaryAI(false); toast('已采用建议') }}>采用建议</button></div>
          </AICard>
        )}

        {/* 简历上传（整合进补信息流） */}
        <ResumeUploadInline hasResume={hasResume} />
      </div>
      <div className="page-foot">
        <div style={{ width: '100%', textAlign: 'center' }}>
          {!hasResume && (
            <div className="ai-tip" style={{ fontSize: 12, marginBottom: 8 }}>
              ⚡ 投递简历前还需要上传简历哦，请在上方上传
            </div>
          )}
          <button className="btn btn-primary" onClick={() => {
            markCompleted()
            toast('信息已保存' + (!hasResume ? '，还需上传简历才能投递' : ''), '✓')
            setTimeout(() => navigate(-1), 700)
          }}>提交并查看完整信息</button>
        </div>
      </div>
    </>
  )
}

function PubCell({ label, req, value, on, onToggle }) {
  return (
    <div className="form-cell" style={{ alignItems: 'center' }}>
      <span className={`fc-label ${req ? 'req' : ''}`}>{label}</span>
      <div className="fc-body row between" style={{ alignItems: 'center' }}>
        <span>{value}</span>
        <div className="row gap6" style={{ flexShrink: 0 }}>
          <span className="tiny muted">{on ? '招聘者可见' : '仅自己'}</span>
          <Switch on={on} onClick={onToggle} />
        </div>
      </div>
    </div>
  )
}

/* ============ 补信息流内简历上传组件 ============ */
function ResumeUploadInline({ hasResume }) {
  const { markResume } = useProfile()
  const navigate = useNavigate()
  const [stage, setStage] = useState(hasResume ? 'done' : 'idle') // idle | uploading | parsing | done

  const startUpload = () => {
    setStage('uploading')
    // mock 选择文件后立即进入解析
    setTimeout(() => setStage('parsing'), 600)
    setTimeout(() => { setStage('done'); markResume() }, 2400)
  }

  return (
    <>
      <div className="cell-group-title">简历（必传）</div>
      <div className="cell-group">
        <div style={{ padding: 14 }}>
          {stage === 'idle' && (
            <div onClick={startUpload}
              style={{ border: '1.5px dashed var(--wx-line)', borderRadius: 10, padding: '18px 14px', textAlign: 'center', cursor: 'pointer', background: '#FAFAFA' }}>
              <div style={{ fontSize: 28, marginBottom: 6 }}>📄</div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>上传简历</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>支持 PDF / 图片，AI 自动解析并填充能力信息</div>
              <AIBadge soft>AI 解析</AIBadge>
            </div>
          )}
          {stage === 'uploading' && (
            <div style={{ border: '1.5px dashed var(--wx-line)', borderRadius: 10, padding: '18px 14px', textAlign: 'center', background: '#FAFAFA' }}>
              <span className="spin" style={{ width: 20, height: 20, display: 'inline-block' }} />
              <div style={{ fontSize: 13, marginTop: 4 }}>上传中…</div>
            </div>
          )}
          {stage === 'parsing' && (
            <div style={{ border: '1.5px dashed var(--wx-green)', borderRadius: 10, padding: '18px 14px', textAlign: 'center', background: 'var(--ai-bg)' }}>
              <span className="spin" style={{ width: 20, height: 20, display: 'inline-block' }} />
              <div style={{ fontSize: 13, marginTop: 4, color: 'var(--wx-green-dark)' }}>AI 正在解析简历…</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>提取基本信息 / 工作经历 / 技能</div>
            </div>
          )}
          {stage === 'done' && (
            <div style={{ border: '1.5px solid var(--wx-green)', borderRadius: 10, padding: '14px', background: 'var(--ai-bg)' }}>
              <div className="row between">
                <span style={{ fontSize: 14, color: 'var(--wx-green-dark)' }}>✅ 简历已上传并解析</span>
                <span className="tiny" style={{ color: 'var(--wx-green-dark)', cursor: 'pointer', textDecoration: 'underline' }}
                  onClick={() => navigate('/seeker/portrait')}>查看画像 ›</span>
              </div>
              <div className="tiny muted" style={{ marginTop: 4 }}>李然 · 5年前端 · React/TypeScript/Node.js</div>
              <div className="row gap6" style={{ marginTop: 6 }}>
                <span className="tag tag-green" style={{ fontSize: 11 }}>React</span>
                <span className="tag tag-green" style={{ fontSize: 11 }}>TypeScript</span>
                <span className="tag tag-green" style={{ fontSize: 11 }}>前端工程化</span>
                <span className="ai-badge soft" style={{ fontSize: 10 }}>AI解析</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

/* ============ 应聘者对话（AI 润色 + 面试识别 + 交换联系方式） ============ */
export function SeekerChat() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const chat = getSeekerChat(id) || getSeekerChat('101')
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
      <NavBar title={chat.name} />
      <div className="page chat-page" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="grow" style={{ overflowY: 'auto', paddingBottom: 8 }}>
          <div className="ai-tip center" style={{ padding: '10px 0' }}>关于「{chat.job}」的沟通</div>
          {msgs.map((m, i) => (
            <div key={i} className={`msg ${m.from}`}>
              {m.from === 'them' && <span className="avatar" style={{ background: pickColor(chat.logoIdx) }}>{chat.name[0]}</span>}
              <div>
                <div className="bubble">
                  {m.text}
                  {m.isInterview && <div className="interview-flag">📅 疑似面试邀约 · <span style={{ textDecoration: 'underline' }}>确认面试</span></div>}
                </div>
              </div>
            </div>
          ))}
          {exchanged && (
            <div style={{ margin: '12px 16px', padding: '14px', background: 'linear-gradient(135deg,#ECF9F1,#E8F5FF)', borderRadius: 10, textAlign: 'center' }}>
              <div style={{ fontSize: 28, marginBottom: 6 }}>🤝</div>
              <div style={{ fontWeight: 600, color: 'var(--wx-green-dark)', fontSize: 14 }}>对接成功！</div>
              <div className="tiny muted" style={{ marginTop: 4, lineHeight: 1.6 }}>
                对方企业邮箱：hr@xingchen.com<br />
                可通过邮箱直接联系，约定面试时间
              </div>
            </div>
          )}
        </div>

        {/* AI 回复建议（润色后的回复） */}
        {showAI && (
          <div className="ai-suggests">
            <div className="as-hd">⚡ AI 建议回复（已优化措辞）</div>
            <div className="as-item" onClick={() => send(aiMock.seekerPolish)}>
              <span className="as-style">专业 · 得体</span>{aiMock.seekerPolish}
            </div>
          </div>
        )}

        <div className="chat-bar">
          <div className="row gap8" style={{ marginBottom: 8 }}>
            <button className="ai-btn" onClick={() => setShowAI(s => !s)}>⚡ AI 润色/回复</button>
            {!exchanged && <button className="ai-btn" style={{ color: 'var(--wx-blue)', borderColor: '#BEE3FA', background: '#EFF8FF' }} onClick={() => { setExchanged(true); toast('对方已确认，联系方式已互换', '🤝') }}>🤝 请求交换联系方式</button>}
          </div>
          <div className="cb-input-row">
            <div className="cb-input" contentEditable suppressContentEditableWarning onInput={e => setInput(e.currentTarget.textContent)} style={{ minHeight: 20 }} />
            <button className="cb-send" onClick={() => send(input)}>发送</button>
          </div>
        </div>
      </div>
    </>
  )
}
