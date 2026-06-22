import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, useToast } from '../components/ui.jsx'
import { getJobForAdmin, listJobsForAdmin, reviewJob } from '../services/index.js'

function salaryText(job) {
  if (!job) return '-'
  return `${job.salary_min}K-${job.salary_max}K`
}

function statusText(status) {
  return {
    draft: '草稿',
    pending: '待审核',
    active: '已上线',
    closed: '已关闭',
    rejected: '已驳回',
  }[status] || status || '-'
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '-'
}

export function AdminReviewList() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    setLoading(true)
    listJobsForAdmin({ status: 'pending', limit: 100 })
      .then(data => {
        if (!alive) return
        setJobs(data.items || [])
        setError('')
      })
      .catch(err => {
        if (!alive) return
        setJobs([])
        setError(err.message || '审核队列加载失败')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => { alive = false }
  }, [])

  return (
    <>
      <NavBar title="审核队列" />
      <div style={{ paddingBottom: 60 }}>
        <div style={{ padding: '12px 16px', background: 'var(--wx-bg)', borderBottom: '1px solid var(--wx-line)' }}>
          <span className="tiny muted">{loading ? '加载中...' : `待审核 ${jobs.length} 条`}</span>
        </div>
        {error && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>}
        <div className="cell-group">
          {jobs.map(job => (
            <div
              key={job.id}
              className="cell link"
              onClick={() => navigate(`/admin/review/${job.id}`)}
              style={{ alignItems: 'flex-start', paddingTop: 14, paddingBottom: 14 }}
            >
              <div className="grow">
                <div className="row between">
                  <span style={{ fontWeight: 600, fontSize: 14 }}>{job.title}</span>
                  <span className="tiny muted">{formatDate(job.created_at)}</span>
                </div>
                <div className="tiny muted" style={{ marginTop: 4 }}>
                  {job.recruiter_display_name || '招聘者'} · {job.city} · {salaryText(job)}
                </div>
                <div style={{ marginTop: 8 }}>
                  <span className="tag tag-blue" style={{ fontSize: 11 }}>{statusText(job.status)}</span>
                </div>
              </div>
              <span className="cell-arrow">›</span>
            </div>
          ))}
        </div>
        {!loading && !error && jobs.length === 0 && (
          <div className="empty" style={{ paddingTop: 100 }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>✓</div>
            <div>暂无待审核岗位</div>
          </div>
        )}
      </div>
    </>
  )
}

export function AdminReviewDetail() {
  const navigate = useNavigate()
  const { id } = useParams()
  const toast = useToast()
  const [job, setJob] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const loadJob = () => {
    setLoading(true)
    getJobForAdmin(id)
      .then(data => {
        setJob(data)
        setError('')
      })
      .catch(err => {
        setJob(null)
        setError(err.message || '审核详情加载失败')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadJob()
  }, [id])

  const submitReview = async (action) => {
    if (submitting || !job) return
    if (action === 'reject' && !rejectReason.trim()) {
      toast('请填写驳回原因')
      return
    }
    setSubmitting(true)
    try {
      await reviewJob(job.id, action === 'approve'
        ? { action: 'approve' }
        : { action: 'reject', reject_reason: rejectReason.trim() })
      toast(action === 'approve' ? '岗位已通过' : '岗位已驳回')
      setShowRejectModal(false)
      setTimeout(() => navigate('/admin'), 800)
    } catch (err) {
      toast(err.message || '审核失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <NavBar title="岗位审核详情" />
      <div style={{ paddingBottom: 80 }}>
        {loading && <div className="ai-tip" style={{ margin: 16 }}>加载审核详情中...</div>}
        {error && <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>{error}</div>}

        {!loading && job && (
          <>
            <div className="cell-group-title">岗位信息</div>
            <div className="cell-group">
              <div className="cell"><span className="cell-label">岗位名称</span><span>{job.title}</span></div>
              <div className="cell"><span className="cell-label">薪资范围</span><span>{salaryText(job)}</span></div>
              <div className="cell"><span className="cell-label">工作城市</span><span>{job.city}</span></div>
              <div className="cell"><span className="cell-label">经验要求</span><span>{job.experience}</span></div>
              <div className="cell"><span className="cell-label">学历要求</span><span>{job.education}</span></div>
              <div className="cell"><span className="cell-label">发布企业</span><span>{job.recruiter_display_name || '-'}</span></div>
              <div className="cell"><span className="cell-label">当前状态</span><span>{statusText(job.status)}</span></div>
              <div className="cell"><span className="cell-label">提交时间</span><span className="tiny muted">{formatDate(job.created_at)}</span></div>
            </div>

            <div className="cell-group-title">岗位标签</div>
            <div className="cell-group">
              <div style={{ padding: 16 }}>
                {(job.tags || []).length > 0
                  ? job.tags.map(tag => <span key={tag} className="tag tag-green" style={{ marginRight: 6 }}>{tag}</span>)
                  : <span className="tiny muted">暂无标签</span>}
              </div>
            </div>

            <div className="cell-group-title">工作职责</div>
            <div style={{ padding: 16, background: 'white', borderBottom: '8px solid var(--wx-bg)' }}>
              <div className="tiny" style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{job.description}</div>
            </div>

            <div className="cell-group-title">任职要求</div>
            <div style={{ padding: 16, background: 'white', borderBottom: '8px solid var(--wx-bg)' }}>
              <div className="tiny" style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{job.requirement}</div>
            </div>

            {job.benefits && (
              <>
                <div className="cell-group-title">福利待遇</div>
                <div style={{ padding: 16, background: 'white', borderBottom: '8px solid var(--wx-bg)' }}>
                  <div className="tiny" style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{job.benefits}</div>
                </div>
              </>
            )}

            {job.reject_reason && (
              <div className="ai-tip" style={{ margin: 16, color: 'var(--wx-red)' }}>
                驳回原因：{job.reject_reason}
              </div>
            )}
          </>
        )}
      </div>

      {job?.status === 'pending' && (
        <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, background: 'white', padding: 12, borderTop: '1px solid var(--wx-line)', display: 'flex', gap: 12 }}>
          <button className="btn btn-default grow" disabled={submitting} onClick={() => setShowRejectModal(true)}>驳回</button>
          <button className="btn btn-primary grow" disabled={submitting} onClick={() => submitReview('approve')}>
            {submitting ? '处理中...' : '通过'}
          </button>
        </div>
      )}

      {showRejectModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999 }} onClick={() => setShowRejectModal(false)}>
          <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, background: 'white', borderRadius: '16px 16px 0 0', padding: 20 }} onClick={e => e.stopPropagation()}>
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>驳回原因</div>
            <textarea
              placeholder="请填写驳回原因"
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              style={{ width: '100%', minHeight: 120, padding: 12, border: '1px solid var(--wx-line)', borderRadius: 8, fontSize: 14, resize: 'vertical', boxSizing: 'border-box' }}
            />
            <div className="row gap12" style={{ marginTop: 16 }}>
              <button className="btn btn-weak grow" disabled={submitting} onClick={() => setShowRejectModal(false)}>取消</button>
              <button className="btn btn-primary grow" disabled={submitting} onClick={() => submitReview('reject')}>
                {submitting ? '处理中...' : '确认驳回'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
