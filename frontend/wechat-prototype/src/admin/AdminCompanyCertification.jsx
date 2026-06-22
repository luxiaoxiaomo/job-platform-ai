import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, AIBadge, useToast } from '../components/ui.jsx'
import {
  listCompanyCertifications,
  getCompanyCertification,
  getCurrentUser,
  logout,
  reviewCompanyCertification,
} from '../services/index.js'
import { API_BASE_URL } from '../services/api.js'

/**
 * 企业认证审核列表（管理员）
 * 真实API联调版
 */
export function AdminCompanyCertificationList() {
  const navigate = useNavigate()
  const toast = useToast()

  const [list, setList] = useState([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState('pending')

  // 加载列表
  useEffect(() => {
    loadList()
  }, [statusFilter])

  const loadList = async () => {
    try {
      setLoading(true)
      const response = await listCompanyCertifications({
        status: statusFilter,
        skip: 0,
        limit: 50,
      })
      setList(response.items || [])
    } catch (error) {
      console.error('加载审核列表失败:', error)
      toast(error.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const getStatusLabel = (status) => {
    switch (status) {
      case 'pending': return '待审核'
      case 'approved': return '已通过'
      case 'rejected': return '已驳回'
      default: return status
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'var(--wx-orange)'
      case 'approved': return 'var(--wx-green)'
      case 'rejected': return 'var(--wx-red)'
      default: return 'var(--wx-text-2)'
    }
  }

  const getMethodLabel = (method) => {
    switch (method) {
      case 'enterprise_email': return '企业邮箱'
      case 'hr_authorization': return 'HR授权'
      default: return '营业执照'
    }
  }

  return (
    <>
      <NavBar title="企业认证审核" onBack={() => navigate('/admin')} />
      <div style={{ paddingBottom: 60 }}>
        {/* 状态筛选 */}
        <div style={{ padding: '12px 16px', background: 'white', borderBottom: '1px solid var(--wx-line)' }}>
          <div className="row gap8">
            {['pending', 'approved', 'rejected'].map(s => (
              <span
                key={s}
                className={`tag ${statusFilter === s ? 'tag-green' : 'tag-gray'}`}
                style={{ cursor: 'pointer' }}
                onClick={() => setStatusFilter(s)}
              >
                {getStatusLabel(s)}
              </span>
            ))}
          </div>
        </div>

        {/* 真实API标记 */}
        {import.meta.env.VITE_USE_MOCK === 'false' && (
          <div className="ai-tip" style={{ margin: '8px 16px' }}>
            <AIBadge soft>真实API</AIBadge>
            <span style={{ marginLeft: 6 }}>连接真实后端审核系统</span>
          </div>
        )}

        {/* 加载中 */}
        {loading && (
          <div className="center" style={{ padding: 60 }}>
            <div className="spin" style={{ width: 32, height: 32 }} />
            <div className="tiny muted" style={{ marginTop: 12 }}>加载中...</div>
          </div>
        )}

        {/* 列表 */}
        {!loading && (
          <div className="cell-group">
            {list.map(item => (
              <div
                key={item.id}
                className="cell link"
                onClick={() => navigate(`/admin/company-certification/${item.id}`)}
                style={{ alignItems: 'flex-start', paddingTop: 14, paddingBottom: 14 }}
              >
                <div className="grow">
                  <div className="row between">
                    <span style={{ fontWeight: 600, fontSize: 14 }}>
                      🏢 {item.company_name || '未填写'}
                    </span>
                    <span className="tiny" style={{ color: getStatusColor(item.status) }}>
                      {getStatusLabel(item.status)}
                    </span>
                  </div>
                  <div className="tiny muted" style={{ marginTop: 4 }}>
                    招聘者：{item.recruiter_display_name || `用户${item.recruiter_id}`}
                  </div>
                  <div className="tiny muted" style={{ marginTop: 4 }}>
                    认证方式：{getMethodLabel(item.verification_method)}
                  </div>
                  <div className="tiny muted" style={{ marginTop: 4 }}>
                    信用代码：{item.unified_social_credit_code || '-'}
                  </div>
                  <div className="tiny muted" style={{ marginTop: 4 }}>
                    提交时间：{item.created_at ? new Date(item.created_at).toLocaleString('zh-CN') : '-'}
                  </div>
                </div>
                <span className="cell-arrow">›</span>
              </div>
            ))}

            {list.length === 0 && (
              <div className="empty" style={{ paddingTop: 60, paddingBottom: 60 }}>
                <div style={{ fontSize: 48, marginBottom: 12 }}>
                  {statusFilter === 'pending' ? '✅' : '📋'}
                </div>
                <div className="tiny muted">
                  {statusFilter === 'pending' ? '暂无待审核项' : `暂无${getStatusLabel(statusFilter)}的认证`}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  )
}

/**
 * 企业认证审核详情（管理员）
 * 真实API联调版
 */
export function AdminCompanyCertificationDetail() {
  const navigate = useNavigate()
  const { id } = useParams()
  const toast = useToast()

  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  // 加载详情
  useEffect(() => {
    loadDetail()
  }, [id])

  const loadDetail = async () => {
    try {
      setLoading(true)
      const data = await getCompanyCertification(id)
      setDetail(data)
    } catch (error) {
      console.error('加载详情失败:', error)
      toast(error.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 通过审核
  const handleApprove = async () => {
    try {
      setProcessing(true)
      await reviewCompanyCertification(id, {
        action: 'approve',
      })
      toast('审核通过 ✓')
      setTimeout(() => navigate('/admin/company-certifications'), 800)
    } catch (error) {
      toast(error.message || '操作失败')
    } finally {
      setProcessing(false)
    }
  }

  // 驳回审核
  const handleReject = async () => {
    if (!rejectReason.trim()) {
      toast('请填写驳回原因')
      return
    }

    try {
      setProcessing(true)
      await reviewCompanyCertification(id, {
        action: 'reject',
        reject_reason: rejectReason.trim(),
      })
      toast('已驳回')
      setShowRejectModal(false)
      setTimeout(() => navigate('/admin/company-certifications'), 800)
    } catch (error) {
      toast(error.message || '操作失败')
    } finally {
      setProcessing(false)
    }
  }

  if (loading) {
    return (
      <>
        <NavBar title="审核详情" onBack={() => navigate(-1)} />
        <div className="center" style={{ paddingTop: 100 }}>
          <div className="spin" style={{ width: 32, height: 32 }} />
          <div className="tiny muted" style={{ marginTop: 12 }}>加载中...</div>
        </div>
      </>
    )
  }

  if (!detail) {
    return (
      <>
        <NavBar title="审核详情" onBack={() => navigate(-1)} />
        <div className="center" style={{ paddingTop: 100 }}>
          <div className="tiny muted">认证记录不存在</div>
        </div>
      </>
    )
  }

  const isPending = detail.status === 'pending'
  const licenseUrl = detail.license_file_url
    ? `${API_BASE_URL}${detail.license_file_url}`
    : ''

  return (
    <>
      <NavBar title="审核详情" onBack={() => navigate(-1)} />
      <div style={{ paddingBottom: isPending ? 80 : 16 }}>
        {/* 状态卡片 */}
        <div style={{ background: 'white', padding: 16, borderBottom: '8px solid var(--wx-bg)' }}>
          <div className="row between">
            <div>
              <div style={{ fontSize: 18, fontWeight: 600 }}>{detail.company_name || '-'}</div>
              <div className="tiny muted" style={{ marginTop: 4 }}>
                招聘者：{detail.recruiter_display_name || `用户${detail.recruiter_id}`}
              </div>
            </div>
            <span className={`tag ${
              detail.status === 'pending' ? 'tag-orange' :
              detail.status === 'approved' ? 'tag-green' :
              'tag-red'
            }`}>
              {detail.status === 'pending' ? '待审核' :
               detail.status === 'approved' ? '已通过' :
               '已驳回'}
            </span>
          </div>

          {detail.status === 'rejected' && detail.reject_reason && (
            <div style={{ marginTop: 12, padding: 10, background: '#FFF0F0', borderRadius: 6 }}>
              <div className="tiny" style={{ color: 'var(--wx-red)', fontWeight: 500 }}>驳回原因</div>
              <div className="tiny" style={{ marginTop: 4, color: 'var(--wx-text)' }}>
                {detail.reject_reason}
              </div>
            </div>
          )}
        </div>

        {/* 企业信息 */}
        <div className="cell-group-title">企业信息</div>
        <div className="cell-group">
          <div className="cell">
            <span className="cell-label">企业名称</span>
            <span>{detail.company_name || '-'}</span>
          </div>
          <div className="cell">
            <span className="cell-label">统一社会信用代码</span>
            <span className="tiny">{detail.unified_social_credit_code || '-'}</span>
          </div>
          <div className="cell">
            <span className="cell-label">法定代表人</span>
            <span>{detail.legal_representative || '-'}</span>
          </div>
          <div className="cell">
            <span className="cell-label">注册地址</span>
            <span className="tiny">{detail.registered_address || '-'}</span>
          </div>
        </div>

        {/* 营业执照 */}
        {detail.license_file_url && (
          <>
            <div className="cell-group-title">营业执照</div>
            <div style={{ padding: 16, background: 'white' }}>
              <div className="tiny muted" style={{ marginBottom: 8 }}>
                文件：{detail.license_file_name}
              </div>
              {detail.license_file_url.match(/\.(jpg|jpeg|png|webp|bmp)$/i) ? (
                <img
                  src={licenseUrl}
                  alt="营业执照"
                  style={{ width: '100%', borderRadius: 8 }}
                />
              ) : (
                <a
                  href={licenseUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-default btn-sm"
                >
                  📄 查看文件
                </a>
              )}
            </div>
          </>
        )}

        {/* 审核信息 */}
        <div className="cell-group-title">审核信息</div>
        <div className="cell-group">
          <div className="cell">
            <span className="cell-label">提交时间</span>
            <span className="tiny">
              {detail.created_at ? new Date(detail.created_at).toLocaleString('zh-CN') : '-'}
            </span>
          </div>
          {detail.reviewed_at && (
            <div className="cell">
              <span className="cell-label">审核时间</span>
              <span className="tiny">
                {new Date(detail.reviewed_at).toLocaleString('zh-CN')}
              </span>
            </div>
          )}
          {detail.reviewer_id && (
            <div className="cell">
              <span className="cell-label">审核人ID</span>
              <span className="tiny">{detail.reviewer_id}</span>
            </div>
          )}
        </div>
      </div>

      {/* 底部操作栏（仅待审核时显示） */}
      {isPending && (
        <div style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          background: 'white',
          padding: 12,
          borderTop: '1px solid var(--wx-line)',
          display: 'flex',
          gap: 12
        }}>
          <button
            className={`btn ${processing ? 'btn-disabled' : 'btn-default'} grow`}
            onClick={() => setShowRejectModal(true)}
            disabled={processing}
          >
            ❌ 驳回
          </button>
          <button
            className={`btn ${processing ? 'btn-disabled' : 'btn-primary'} grow`}
            onClick={handleApprove}
            disabled={processing}
          >
            {processing ? '处理中...' : '✅ 通过'}
          </button>
        </div>
      )}

      {/* 驳回原因弹窗 */}
      {showRejectModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            zIndex: 9999
          }}
          onClick={() => setShowRejectModal(false)}
        >
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              background: 'white',
              borderRadius: '16px 16px 0 0',
              padding: 20
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>驳回原因</div>
            <textarea
              placeholder="请填写驳回原因（必填）"
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              style={{
                width: '100%',
                minHeight: 120,
                padding: 12,
                border: '1px solid var(--wx-line)',
                borderRadius: 8,
                fontSize: 14,
                resize: 'vertical'
              }}
            />
            <div className="row gap12" style={{ marginTop: 16 }}>
              <button
                className="btn btn-weak grow"
                onClick={() => setShowRejectModal(false)}
                disabled={processing}
              >
                取消
              </button>
              <button
                className={`btn ${processing ? 'btn-disabled' : 'btn-primary'} grow`}
                onClick={handleReject}
                disabled={processing}
              >
                {processing ? '处理中...' : '确认驳回'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export function AdminCompanyCertificationDesktopDetail() {
  const navigate = useNavigate()
  const { id } = useParams()
  const toast = useToast()
  const currentUser = getCurrentUser()
  const adminName = currentUser?.display_name || currentUser?.phone || 'admin'

  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)

  useEffect(() => {
    loadDetail()
  }, [id])

  const loadDetail = async () => {
    try {
      setLoading(true)
      const data = await getCompanyCertification(id)
      setDetail(data)
    } catch (error) {
      console.error('加载详情失败:', error)
      toast(error.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    try {
      setProcessing(true)
      await reviewCompanyCertification(id, { action: 'approve' })
      toast('企业认证已通过')
      navigate('/admin')
    } catch (error) {
      toast(error.message || '审核失败')
    } finally {
      setProcessing(false)
    }
  }

  const handleReject = async () => {
    const reason = window.prompt('请输入驳回原因', '营业执照或企业信息需补充核对')
    if (!reason || !reason.trim()) return

    try {
      setProcessing(true)
      await reviewCompanyCertification(id, {
        action: 'reject',
        reject_reason: reason.trim(),
      })
      toast('企业认证已驳回')
      navigate('/admin')
    } catch (error) {
      toast(error.message || '审核失败')
    } finally {
      setProcessing(false)
    }
  }

  const statusLabel = (status) => {
    if (status === 'pending') return '待审核'
    if (status === 'approved') return '已通过'
    if (status === 'rejected') return '已驳回'
    return status || '-'
  }

  const statusClass = (status) => {
    if (status === 'approved') return 'pass'
    if (status === 'rejected') return 'block'
    return 'warn'
  }

  const methodLabel = (method) => {
    if (method === 'enterprise_email') return '企业邮箱'
    if (method === 'hr_authorization') return 'HR授权'
    return '营业执照'
  }

  const renderFilePreview = (url, name, label) => {
    const isImage = /\.(jpg|jpeg|png|webp|bmp)$/i.test(url || '')
    const isPdf = /\.pdf$/i.test(url || '')
    if (!url) return <div style={{ color: 'var(--a-text-2)' }}>未上传{label}</div>
    if (isImage) {
      return (
        <div style={{ border: '1px solid var(--a-line)', borderRadius: 8, overflow: 'hidden', background: '#FAFBFC' }}>
          <img src={url} alt={label} style={{ display: 'block', width: '100%', maxHeight: 560, objectFit: 'contain' }} />
        </div>
      )
    }
    if (isPdf) {
      return (
        <iframe
          title={`${label} PDF`}
          src={url}
          style={{ width: '100%', height: 560, border: '1px solid var(--a-line)', borderRadius: 8, background: '#fff' }}
        />
      )
    }
    return <a className="a-btn primary" href={url} target="_blank" rel="noopener noreferrer">打开{name || label}</a>
  }

  const licenseUrl = detail?.license_file_url
    ? `${API_BASE_URL}${detail.license_file_url}`
    : ''
  const proofUrl = detail?.proof_file_url
    ? `${API_BASE_URL}${detail.proof_file_url}`
    : ''
  const isPending = detail?.status === 'pending'

  return (
    <div className="admin">
      <aside className="admin-side">
        <div className="admin-brand"><span className="dot" />空岗平台 · 运营后台</div>
        <nav className="admin-nav">
          <div className="nav-item" onClick={() => navigate('/admin')}><span className="ico">📊</span>数据概览</div>
          <div className="nav-item active" onClick={() => navigate('/admin')}><span className="ico">✅</span>审核管理</div>
          <div className="nav-item" onClick={() => navigate('/admin')}><span className="ico">👥</span>用户管理</div>
          <div className="nav-item" onClick={() => navigate('/admin')}><span className="ico">⚡</span>AI 监控</div>
          <div className="nav-item" onClick={() => navigate('/admin')}><span className="ico">🗂</span>基础数据</div>
        </nav>
        <div className="admin-side-foot" onClick={() => navigate('/admin')}>← 返回审核列表</div>
      </aside>

      <main className="admin-main">
        <header className="admin-topbar">
          <span className="at-title">企业认证审核详情</span>
          <div className="at-right">
            <span className="admin-user-label">管理员 · {adminName}</span>
            <button type="button" className="admin-logout-btn" onClick={logout}>退出登录</button>
          </div>
        </header>

        <div className="admin-content">
          {loading ? (
            <div className="admin-card">加载认证详情中...</div>
          ) : !detail ? (
            <div className="admin-card">认证记录不存在</div>
          ) : (
            <>
              <div className="admin-card" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>{detail.company_name || '-'}</div>
                  <div style={{ marginTop: 6, color: 'var(--a-text-2)' }}>
                    提交人：{detail.recruiter_display_name || `用户${detail.recruiter_id}`} ·
                    提交时间：{detail.created_at ? new Date(detail.created_at).toLocaleString('zh-CN') : '-'}
                  </div>
                </div>
                <span className={`a-tag ${statusClass(detail.status)}`}>{statusLabel(detail.status)}</span>
                <span className="a-btn" onClick={() => navigate('/admin')}>返回列表</span>
                {isPending && (
                  <>
                    <span className="a-btn danger" onClick={handleReject}>驳回</span>
                    <span className="a-btn primary" onClick={handleApprove}>
                      {processing ? '处理中...' : '通过'}
                    </span>
                  </>
                )}
              </div>

              <div className="admin-grid2" style={{ alignItems: 'start' }}>
                <div className="admin-card">
                  <div className="ac-title">企业信息</div>
                  <table className="admin-table">
                    <tbody>
                      <tr><th>认证方式</th><td><span className="a-tag blue">{methodLabel(detail.verification_method)}</span></td></tr>
                      <tr><th>企业名称</th><td>{detail.company_name || '-'}</td></tr>
                      <tr><th>统一社会信用代码</th><td style={{ fontFamily: 'monospace' }}>{detail.unified_social_credit_code || '-'}</td></tr>
                      <tr><th>法定代表人</th><td>{detail.legal_representative || '-'}</td></tr>
                      <tr><th>注册地址</th><td>{detail.registered_address || '-'}</td></tr>
                      <tr><th>企业邮箱</th><td>{detail.work_email || '-'}</td></tr>
                      <tr><th>申请人</th><td>{detail.applicant_name || '-'}</td></tr>
                      <tr><th>申请人职位</th><td>{detail.applicant_title || '-'}</td></tr>
                      <tr><th>联系电话</th><td>{detail.applicant_phone || '-'}</td></tr>
                      {detail.verification_note && <tr><th>补充说明</th><td>{detail.verification_note}</td></tr>}
                    </tbody>
                  </table>
                </div>

                <div className="admin-card">
                  <div className="ac-title">{detail.verification_method === 'hr_authorization' ? '授权证明材料' : '营业执照'}</div>
                  <div style={{ color: 'var(--a-text-2)', fontSize: 13, marginBottom: 12 }}>
                    文件：{detail.verification_method === 'hr_authorization' ? detail.proof_file_name || '-' : detail.license_file_name || '-'}
                  </div>
                  {detail.verification_method === 'hr_authorization'
                    ? renderFilePreview(proofUrl, detail.proof_file_name, '授权证明材料')
                    : renderFilePreview(licenseUrl, detail.license_file_name, '营业执照')}
                </div>
              </div>

              <div className="admin-card">
                <div className="ac-title">审核信息</div>
                <table className="admin-table">
                  <tbody>
                    <tr><th>当前状态</th><td><span className={`a-tag ${statusClass(detail.status)}`}>{statusLabel(detail.status)}</span></td></tr>
                    <tr><th>审核人 ID</th><td>{detail.reviewer_id || '-'}</td></tr>
                    <tr><th>审核时间</th><td>{detail.reviewed_at ? new Date(detail.reviewed_at).toLocaleString('zh-CN') : '-'}</td></tr>
                    {detail.reject_reason && <tr><th>驳回原因</th><td>{detail.reject_reason}</td></tr>}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
