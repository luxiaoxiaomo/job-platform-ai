import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, useToast } from '../components/ui.jsx'
import { RecruiterBottomNav } from './RecruiterBottomNav.jsx'
import { interviews } from '../mock/data.js'

export function RecruiterInterviews() {
  const navigate = useNavigate()
  const [list, setList] = useState(interviews)

  const scheduled = list.filter(i => i.status === 'scheduled')
  const completed = list.filter(i => i.status === 'completed')

  return (<>
    <NavBar title="面试管理" />
    <div style={{ paddingBottom: 60 }}>
      {/* 待面试 */}
      <div className="cell-group-title">待面试 ({scheduled.length})</div>
      <div className="cell-group">
        {scheduled.map(i => (
          <div
            key={i.id}
            className="cell link"
            onClick={() => navigate(`/recruiter/interview/${i.id}`)}
            style={{ alignItems: 'flex-start', paddingTop: 14, paddingBottom: 14 }}
          >
            <div className="grow">
              <div className="row between">
                <span style={{ fontWeight: 600, fontSize: 14 }}>{i.seekerName}</span>
                <span className="tag tag-blue">{i.type}</span>
              </div>
              <div className="tiny muted" style={{ marginTop: 4 }}>{i.jobTitle}</div>
              <div className="tiny" style={{ marginTop: 8, color: 'var(--wx-blue)' }}>
                📅 {i.scheduledAt} · 📍 {i.location}
              </div>
              <div className="tiny muted" style={{ marginTop: 4 }}>面试官：{i.interviewer}</div>
            </div>
            <span className="cell-arrow">›</span>
          </div>
        ))}
        {scheduled.length === 0 && (
          <div className="empty" style={{ padding: '30px 0' }}>
            <div className="tiny muted">暂无待面试</div>
          </div>
        )}
      </div>

      {/* 已完成 */}
      <div className="cell-group-title">已完成 ({completed.length})</div>
      <div className="cell-group">
        {completed.map(i => (
          <div
            key={i.id}
            className="cell link"
            onClick={() => navigate(`/recruiter/interview/${i.id}`)}
            style={{ alignItems: 'flex-start', paddingTop: 14, paddingBottom: 14 }}
          >
            <div className="grow">
              <div className="row between">
                <span style={{ fontWeight: 600, fontSize: 14 }}>{i.seekerName}</span>
                <span className={`tag ${i.result === 'pass' ? 'tag-green' : i.result === 'fail' ? 'tag-gray' : 'tag-orange'}`}>
                  {i.result === 'pass' ? '✅ 通过' : i.result === 'fail' ? '❌ 未通过' : '待评估'}
                </span>
              </div>
              <div className="tiny muted" style={{ marginTop: 4 }}>{i.jobTitle} · {i.type}</div>
              <div className="tiny muted" style={{ marginTop: 6 }}>📅 {i.scheduledAt}</div>
            </div>
            <span className="cell-arrow">›</span>
          </div>
        ))}
      </div>
    </div>
    <RecruiterBottomNav />
  </>)
}

export function RecruiterInterviewDetail() {
  const navigate = useNavigate()
  const toast = useToast()
  const { id } = useParams()
  const [interview, setInterview] = useState(interviews.find(i => i.id === parseInt(id)))
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedback, setFeedback] = useState(interview?.feedback || '')
  const [result, setResult] = useState(interview?.result || 'pending')

  if (!interview) return <div>面试记录不存在</div>

  const handleSaveFeedback = () => {
    if (!feedback.trim()) {
      toast('请填写面试反馈')
      return
    }
    setInterview({ ...interview, feedback, result, status: 'completed' })
    setShowFeedback(false)
    toast('面试反馈已保存')
  }

  return (<>
    <NavBar title="面试详情" />
    <div style={{ paddingBottom: 80 }}>
      {/* 候选人信息 */}
      <div className="cell-group-title">候选人信息</div>
      <div className="cell-group">
        <div className="cell link" onClick={() => navigate(`/recruiter/talent/${interview.seekerId}`)}>
          <span className="cell-label">姓名</span>
          <span>{interview.seekerName} ›</span>
        </div>
        <div className="cell">
          <span className="cell-label">应聘岗位</span>
          <span>{interview.jobTitle}</span>
        </div>
      </div>

      {/* 面试安排 */}
      <div className="cell-group-title">面试安排</div>
      <div className="cell-group">
        <div className="cell">
          <span className="cell-label">面试时间</span>
          <span>{interview.scheduledAt}</span>
        </div>
        <div className="cell">
          <span className="cell-label">面试地点</span>
          <span className="tiny">{interview.location}</span>
        </div>
        <div className="cell">
          <span className="cell-label">面试官</span>
          <span>{interview.interviewer}</span>
        </div>
        <div className="cell">
          <span className="cell-label">面试轮次</span>
          <span>第 {interview.round} 轮 · {interview.type}</span>
        </div>
        <div className="cell">
          <span className="cell-label">状态</span>
          <span className={`tag ${interview.status === 'scheduled' ? 'tag-blue' : 'tag-green'}`}>
            {interview.status === 'scheduled' ? '待面试' : '已完成'}
          </span>
        </div>
      </div>

      {/* 面试反馈 */}
      {interview.status === 'completed' && interview.feedback && (
        <>
          <div className="cell-group-title">面试反馈</div>
          <div style={{ background: 'white', padding: 16 }}>
            <div className="row between" style={{ marginBottom: 12 }}>
              <span style={{ fontSize: 14, fontWeight: 600 }}>面试结果</span>
              <span className={`tag ${interview.result === 'pass' ? 'tag-green' : interview.result === 'fail' ? 'tag-gray' : 'tag-orange'}`}>
                {interview.result === 'pass' ? '✅ 通过' : interview.result === 'fail' ? '❌ 未通过' : '待评估'}
              </span>
            </div>
            <div className="tiny" style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{interview.feedback}</div>
          </div>
        </>
      )}

      {interview.notes && (
        <>
          <div className="cell-group-title">备注</div>
          <div style={{ background: 'white', padding: 16 }}>
            <div className="tiny" style={{ lineHeight: 1.8 }}>{interview.notes}</div>
          </div>
        </>
      )}
    </div>

    {/* 底部操作栏 */}
    {interview.status === 'scheduled' && (
      <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, background: 'white', padding: 12, borderTop: '1px solid var(--wx-line)' }}>
        <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => setShowFeedback(true)}>
          记录面试反馈
        </button>
      </div>
    )}

    {interview.status === 'completed' && !interview.feedback && (
      <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, background: 'white', padding: 12, borderTop: '1px solid var(--wx-line)' }}>
        <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => setShowFeedback(true)}>
          补充面试反馈
        </button>
      </div>
    )}

    {/* 面试反馈弹窗 */}
    {showFeedback && (
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999 }} onClick={() => setShowFeedback(false)}>
        <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, background: 'white', borderRadius: '16px 16px 0 0', padding: 20, maxHeight: '80vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>面试反馈</div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, marginBottom: 8 }}>面试结果</div>
            <div className="row gap12">
              <button
                className={`btn btn-sm grow ${result === 'pass' ? 'btn-primary' : 'btn-weak'}`}
                onClick={() => setResult('pass')}
              >
                ✅ 通过
              </button>
              <button
                className={`btn btn-sm grow ${result === 'pending' ? 'btn-primary' : 'btn-weak'}`}
                onClick={() => setResult('pending')}
              >
                ⏳ 待定
              </button>
              <button
                className={`btn btn-sm grow ${result === 'fail' ? 'btn-primary' : 'btn-weak'}`}
                onClick={() => setResult('fail')}
              >
                ❌ 未通过
              </button>
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, marginBottom: 8 }}>面试评价</div>
            <textarea
              placeholder="记录面试表现、技术能力、沟通情况等..."
              value={feedback}
              onChange={e => setFeedback(e.target.value)}
              style={{ width: '100%', minHeight: 150, padding: 12, border: '1px solid var(--wx-line)', borderRadius: 8, fontSize: 14, resize: 'vertical' }}
            />
          </div>

          <div className="row gap12">
            <button className="btn btn-weak grow" onClick={() => setShowFeedback(false)}>取消</button>
            <button className="btn btn-primary grow" onClick={handleSaveFeedback}>保存</button>
          </div>
        </div>
      </div>
    )}
  </>)
}

// 约面试弹窗组件（从人才详情页调用）
export function ScheduleInterviewModal({ seekerId, seekerName, jobId, jobTitle, onClose, onSchedule }) {
  const toast = useToast()
  const [form, setForm] = useState({
    scheduledAt: '',
    location: '',
    interviewer: '',
    round: 1,
    type: '技术面试',
  })

  const handleSubmit = () => {
    if (!form.scheduledAt || !form.location || !form.interviewer) {
      toast('请填写完整信息')
      return
    }
    onSchedule({ ...form, seekerId, seekerName, jobId, jobTitle })
    toast('面试已安排')
    onClose()
  }

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999 }} onClick={onClose}>
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, background: 'white', borderRadius: '16px 16px 0 0', padding: 20, maxHeight: '80vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>邀约面试</div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, marginBottom: 6, color: 'var(--wx-text-2)' }}>候选人</div>
          <div style={{ fontSize: 14 }}>{seekerName}</div>
        </div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, marginBottom: 6, color: 'var(--wx-text-2)' }}>应聘岗位</div>
          <div style={{ fontSize: 14 }}>{jobTitle}</div>
        </div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, marginBottom: 6 }}>面试时间 *</div>
          <input
            type="datetime-local"
            value={form.scheduledAt}
            onChange={e => setForm({ ...form, scheduledAt: e.target.value })}
            style={{ width: '100%', padding: '10px 12px', border: '1px solid var(--wx-line)', borderRadius: 8, fontSize: 14 }}
          />
        </div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, marginBottom: 6 }}>面试地点 *</div>
          <input
            type="text"
            placeholder="例如：杭州市西湖区文三路 XX 大厦 8 楼 或 线上视频面试"
            value={form.location}
            onChange={e => setForm({ ...form, location: e.target.value })}
            style={{ width: '100%', padding: '10px 12px', border: '1px solid var(--wx-line)', borderRadius: 8, fontSize: 14 }}
          />
        </div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, marginBottom: 6 }}>面试官 *</div>
          <input
            type="text"
            placeholder="例如：李经理"
            value={form.interviewer}
            onChange={e => setForm({ ...form, interviewer: e.target.value })}
            style={{ width: '100%', padding: '10px 12px', border: '1px solid var(--wx-line)', borderRadius: 8, fontSize: 14 }}
          />
        </div>

        <div className="row gap12" style={{ marginBottom: 14 }}>
          <div className="grow">
            <div style={{ fontSize: 13, marginBottom: 6 }}>面试轮次</div>
            <select
              value={form.round}
              onChange={e => setForm({ ...form, round: parseInt(e.target.value) })}
              style={{ width: '100%', padding: '10px 12px', border: '1px solid var(--wx-line)', borderRadius: 8, fontSize: 14 }}
            >
              <option value={1}>第 1 轮</option>
              <option value={2}>第 2 轮</option>
              <option value={3}>第 3 轮</option>
            </select>
          </div>
          <div className="grow">
            <div style={{ fontSize: 13, marginBottom: 6 }}>面试类型</div>
            <select
              value={form.type}
              onChange={e => setForm({ ...form, type: e.target.value })}
              style={{ width: '100%', padding: '10px 12px', border: '1px solid var(--wx-line)', borderRadius: 8, fontSize: 14 }}
            >
              <option>技术面试</option>
              <option>HR面试</option>
              <option>终面</option>
            </select>
          </div>
        </div>

        <div className="row gap12">
          <button className="btn btn-weak grow" onClick={onClose}>取消</button>
          <button className="btn btn-primary grow" onClick={handleSubmit}>确认邀约</button>
        </div>
      </div>
    </div>
  )
}
