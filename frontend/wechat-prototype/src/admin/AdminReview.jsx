import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, AIBadge, useToast } from '../components/ui.jsx'
import { reviewQueue } from '../mock/data.js'

export function AdminReviewList() {
  const navigate = useNavigate()
  const [queue, setQueue] = useState(reviewQueue)

  const pending = queue.filter(r => r.status === 'pending')

  return (<>
    <NavBar title="审核队列" />
    <div style={{ paddingBottom: 60 }}>
      <div style={{ padding: '12px 16px', background: 'var(--wx-bg)', borderBottom: '1px solid var(--wx-line)' }}>
        <span className="tiny muted">待审核 {pending.length} 条</span>
      </div>

      <div className="cell-group">
        {pending.map(r => {
          const aiColor = r.aiResult === 'pass' ? 'var(--wx-green)' : r.aiResult === 'warning' ? 'var(--wx-orange)' : 'var(--wx-red)'
          const aiLabel = r.aiResult === 'pass' ? '✅ AI 建议通过' : r.aiResult === 'warning' ? '⚠️ AI 建议人工审核' : '❌ AI 建议驳回'

          return (
            <div
              key={r.id}
              className="cell link"
              onClick={() => navigate(`/admin/review/${r.id}`)}
              style={{ alignItems: 'flex-start', paddingTop: 14, paddingBottom: 14 }}
            >
              <div className="grow">
                <div className="row between">
                  <span style={{ fontWeight: 600, fontSize: 14 }}>
                    {r.type === 'enterprise' ? `🏢 ${r.company}` : `💼 ${r.jobTitle}`}
                  </span>
                  <span className="tiny muted">{r.submittedAt}</span>
                </div>
                <div className="tiny muted" style={{ marginTop: 4 }}>
                  提交人：{r.submitter} · {r.type === 'enterprise' ? '企业认证' : '岗位发布'}
                </div>
                <div style={{ marginTop: 8 }}>
                  <span className="tiny" style={{ color: aiColor, fontWeight: 500 }}>{aiLabel}</span>
                  <span className="tiny muted" style={{ marginLeft: 8 }}>置信度 {Math.round(r.aiConfidence * 100)}%</span>
                </div>
                {r.aiDetail.riskFlags.length > 0 && (
                  <div className="tiny" style={{ marginTop: 6, color: 'var(--wx-red)', background: '#FFF0F0', padding: '4px 8px', borderRadius: 4 }}>
                    ⚠️ {r.aiDetail.riskFlags[0]}
                  </div>
                )}
              </div>
              <span className="cell-arrow">›</span>
            </div>
          )
        })}
      </div>

      {pending.length === 0 && (
        <div className="empty" style={{ paddingTop: 100 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>✅</div>
          <div>暂无待审核项</div>
        </div>
      )}
    </div>
  </>)
}

export function AdminReviewDetail() {
  const navigate = useNavigate()
  const { id } = useParams()
  const toast = useToast()
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  const review = reviewQueue.find(r => r.id === parseInt(id))
  if (!review) return <div>审核项不存在</div>

  const handleApprove = () => {
    toast('审核通过')
    setTimeout(() => navigate('/admin'), 1000)
  }

  const handleReject = () => {
    if (!rejectReason.trim()) {
      toast('请填写驳回原因')
      return
    }
    toast('已驳回')
    setTimeout(() => navigate('/admin'), 1000)
  }

  const aiColor = review.aiResult === 'pass' ? 'var(--wx-green)' : review.aiResult === 'warning' ? 'var(--wx-orange)' : 'var(--wx-red)'

  return (<>
    <NavBar title="审核详情" />
    <div style={{ paddingBottom: 80 }}>
      {/* AI 审核结果 */}
      <div style={{ background: 'white', padding: 16, borderBottom: '8px solid var(--wx-bg)' }}>
        <div className="row gap8" style={{ marginBottom: 12 }}>
          <AIBadge>AI 审核</AIBadge>
          <span style={{ fontSize: 14, fontWeight: 600, color: aiColor }}>
            {review.aiResult === 'pass' ? '✅ 建议通过' : review.aiResult === 'warning' ? '⚠️ 建议人工复核' : '❌ 建议驳回'}
          </span>
        </div>
        <div className="tiny muted" style={{ lineHeight: 1.6 }}>
          AI 置信度：{Math.round(review.aiConfidence * 100)}%
          {review.aiDetail.riskFlags.length > 0 && (
            <div style={{ marginTop: 8, color: 'var(--wx-red)' }}>
              风险标记：{review.aiDetail.riskFlags.join('、')}
            </div>
          )}
        </div>
      </div>

      {/* 企业认证内容 */}
      {review.type === 'enterprise' && (<>
        <div className="cell-group-title">企业信息</div>
        <div className="cell-group">
          <div className="cell">
            <span className="cell-label">企业名称</span>
            <span>{review.company}</span>
          </div>
          <div className="cell">
            <span className="cell-label">统一社会信用代码</span>
            <span className="tiny">{review.creditCode}</span>
          </div>
          <div className="cell">
            <span className="cell-label">法定代表人</span>
            <span>{review.legalPerson}</span>
          </div>
          <div className="cell">
            <span className="cell-label">注册资本</span>
            <span>{review.registeredCapital}</span>
          </div>
          <div className="cell">
            <span className="cell-label">提交人</span>
            <span>{review.submitter}</span>
          </div>
          <div className="cell">
            <span className="cell-label">提交时间</span>
            <span className="tiny muted">{review.submittedAt}</span>
          </div>
        </div>

        <div className="cell-group-title">营业执照</div>
        <div style={{ padding: 16, background: 'white' }}>
          <img src={review.businessLicense} alt="营业执照" style={{ width: '100%', borderRadius: 8 }} />
        </div>

        <div className="cell-group-title">OCR 识别结果</div>
        <div className="cell-group">
          <div className="cell">
            <span className="cell-label">OCR 匹配度</span>
            <span style={{ color: review.aiDetail.ocrMatch >= 0.9 ? 'var(--wx-green)' : 'var(--wx-orange)' }}>
              {Math.round(review.aiDetail.ocrMatch * 100)}%
            </span>
          </div>
          <div className="cell">
            <span className="cell-label">信用代码校验</span>
            <span style={{ color: review.aiDetail.creditCodeValid ? 'var(--wx-green)' : 'var(--wx-red)' }}>
              {review.aiDetail.creditCodeValid ? '✅ 有效' : '❌ 无效'}
            </span>
          </div>
        </div>
      </>)}

      {/* 岗位审核内容 */}
      {review.type === 'job' && (<>
        <div className="cell-group-title">岗位信息</div>
        <div className="cell-group">
          <div className="cell">
            <span className="cell-label">岗位名称</span>
            <span>{review.jobContent.title}</span>
          </div>
          <div className="cell">
            <span className="cell-label">薪资范围</span>
            <span>{review.jobContent.salary}</span>
          </div>
          <div className="cell">
            <span className="cell-label">工作城市</span>
            <span>{review.jobContent.cities.join('、')}</span>
          </div>
          <div className="cell">
            <span className="cell-label">发布企业</span>
            <span>{review.company}</span>
          </div>
          <div className="cell">
            <span className="cell-label">提交人</span>
            <span>{review.submitter}</span>
          </div>
          <div className="cell">
            <span className="cell-label">提交时间</span>
            <span className="tiny muted">{review.submittedAt}</span>
          </div>
        </div>

        <div className="cell-group-title">工作职责</div>
        <div style={{ padding: 16, background: 'white', borderBottom: '8px solid var(--wx-bg)' }}>
          <div className="tiny" style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{review.jobContent.responsibility}</div>
        </div>

        <div className="cell-group-title">任职要求</div>
        <div style={{ padding: 16, background: 'white', borderBottom: '8px solid var(--wx-bg)' }}>
          <div className="tiny" style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{review.jobContent.requirement}</div>
        </div>

        <div className="cell-group-title">AI 内容安全检测</div>
        <div className="cell-group">
          <div className="cell">
            <span className="cell-label">歧视性用语</span>
            <span style={{ color: review.aiDetail.discriminationCheck === 'pass' ? 'var(--wx-green)' : 'var(--wx-red)' }}>
              {review.aiDetail.discriminationCheck === 'pass' ? '✅ 未检测到' : '❌ 检测到问题'}
            </span>
          </div>
          <div className="cell">
            <span className="cell-label">内容合规</span>
            <span style={{ color: review.aiDetail.contentSafe ? 'var(--wx-green)' : 'var(--wx-red)' }}>
              {review.aiDetail.contentSafe ? '✅ 合规' : '❌ 不合规'}
            </span>
          </div>
        </div>
      </>)}
    </div>

    {/* 底部操作栏 */}
    <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, background: 'white', padding: 12, borderTop: '1px solid var(--wx-line)', display: 'flex', gap: 12 }}>
      <button className="btn btn-default grow" onClick={() => setShowRejectModal(true)}>❌ 驳回</button>
      <button className="btn btn-primary grow" onClick={handleApprove}>✅ 通过</button>
    </div>

    {/* 驳回原因弹窗 */}
    {showRejectModal && (
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999 }} onClick={() => setShowRejectModal(false)}>
        <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, background: 'white', borderRadius: '16px 16px 0 0', padding: 20 }} onClick={e => e.stopPropagation()}>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>驳回原因</div>
          <textarea
            placeholder="请填写驳回原因（必填）"
            value={rejectReason}
            onChange={e => setRejectReason(e.target.value)}
            style={{ width: '100%', minHeight: 120, padding: 12, border: '1px solid var(--wx-line)', borderRadius: 8, fontSize: 14, resize: 'vertical' }}
          />
          <div className="row gap12" style={{ marginTop: 16 }}>
            <button className="btn btn-weak grow" onClick={() => setShowRejectModal(false)}>取消</button>
            <button className="btn btn-primary grow" onClick={handleReject}>确认驳回</button>
          </div>
        </div>
      </div>
    )}
  </>)
}
