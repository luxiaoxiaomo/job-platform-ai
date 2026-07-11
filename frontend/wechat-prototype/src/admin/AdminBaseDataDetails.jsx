import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getCurrentUser, getStandardPosition, getTagLibraryItem, listBaseDataOperationLogs, logout } from '../services/index.js'
import { BaseData } from './AdminApp.jsx'
import '../styles/admin.css'

const NAV = [
  { key: 'dash', icon: '📊', label: '数据概览' },
  { key: 'review', icon: '✅', label: '审核管理' },
  { key: 'users', icon: '👥', label: '用户管理' },
  { key: 'ai', icon: '⚡', label: 'AI 监控' },
  { key: 'data-overview', icon: '🗂', label: '基础数据概览' },
  { key: 'data-positions', icon: '💼', label: '标准职位库' },
  { key: 'data-tags', icon: '🏷', label: '标签库', path: '/admin/tags' },
  { key: 'data-rules', icon: '🎯', label: '匹配规则' },
  { key: 'data-logs', icon: '🧾', label: '操作日志' },
  { key: 'data-push', icon: '🔔', label: '推送队列' },
]

function formatAdminDate(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '-'
}

function BaseDataStatusTag({ status }) {
  const active = status === 'active'
  return <span className={`a-tag ${active ? 'pass' : 'gray'}`}>{active ? '启用' : status === 'inactive' ? '停用' : status || '-'}</span>
}

function AdminDetailShell({ title, activePage, backPage, backPath, backText, children }) {
  const navigate = useNavigate()
  const currentUser = getCurrentUser()
  const adminName = currentUser?.display_name || currentUser?.phone || 'admin'

  const goBack = () => {
    if (backPath) {
      navigate(backPath)
      return
    }
    navigate('/admin', { state: { page: backPage } })
  }

  const openNavItem = (item) => {
    if (item.path) {
      navigate(item.path)
      return
    }
    navigate('/admin', { state: { page: item.key } })
  }

  return (
    <div className="admin">
      <aside className="admin-side">
        <div className="admin-brand"><span className="dot" />空岗平台 · 运营后台</div>
        <nav className="admin-nav">
          {NAV.map(item => (
            <div
              key={item.key}
              className={`nav-item ${activePage === item.key ? 'active' : ''}`}
              onClick={() => openNavItem(item)}
            >
              <span className="ico">{item.icon}</span>{item.label}
            </div>
          ))}
        </nav>
        <div className="admin-side-foot" onClick={goBack}>{backText}</div>
      </aside>
      <main className="admin-main">
        <header className="admin-topbar">
          <span className="at-title">{title}</span>
          <div className="at-right">
            <span>管理员 · {adminName}</span>
            <button type="button" className="a-btn sm" onClick={logout}>退出登录</button>
          </div>
        </header>
        <div className="admin-content">{children}</div>
      </main>
    </div>
  )
}

function DetailState({ loading, error, emptyText }) {
  if (loading) {
    return <div className="admin-card"><div style={{ padding: 40, textAlign: 'center', color: 'var(--a-text-2)' }}>加载中...</div></div>
  }
  if (error) {
    return <div className="admin-card"><div style={{ padding: 40, textAlign: 'center', color: '#E54545' }}>{error}</div></div>
  }
  return <div className="admin-card"><div style={{ padding: 40, textAlign: 'center', color: 'var(--a-text-2)' }}>{emptyText}</div></div>
}

function SnapshotSummary({ snapshot }) {
  if (!snapshot) return <span>-</span>
  const keys = ['name', 'category', 'status', 'sort_order', 'parent_id']
  const parts = keys
    .filter(key => snapshot[key] !== undefined && snapshot[key] !== null && snapshot[key] !== '')
    .map(key => `${key}: ${Array.isArray(snapshot[key]) ? snapshot[key].join(', ') : snapshot[key]}`)
  return <span>{parts.length > 0 ? parts.join('；') : JSON.stringify(snapshot)}</span>
}

function BaseDataDetailLogs({ logs }) {
  return (
    <div className="admin-card">
      <div className="ac-title">最近操作日志</div>
      <table className="admin-table">
        <thead>
          <tr>
            <th>动作</th>
            <th>操作人</th>
            <th>变更前</th>
            <th>变更后</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          {logs.length > 0 ? logs.map(log => (
            <tr key={log.id}>
              <td><span className="a-tag blue">{log.action}</span></td>
              <td>{log.actor_id || '-'}</td>
              <td className="tiny muted"><SnapshotSummary snapshot={log.before} /></td>
              <td className="tiny muted"><SnapshotSummary snapshot={log.after} /></td>
              <td>{formatAdminDate(log.created_at)}</td>
            </tr>
          )) : (
            <tr><td colSpan="5" style={{ color: 'var(--a-text-2)' }}>暂无操作日志。</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export function AdminStandardPositionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [position, setPosition] = useState(null)
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        setLoading(true)
        const [detail, logData] = await Promise.all([
          getStandardPosition(id),
          listBaseDataOperationLogs({ resource_type: 'standard_position', resource_id: id, limit: 10 }),
        ])
        if (!alive) return
        setPosition(detail)
        setLogs(logData.items || [])
        setError('')
      } catch (err) {
        if (!alive) return
        setPosition(null)
        setLogs([])
        setError(err.message || '标准职位详情加载失败')
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => { alive = false }
  }, [id])

  return (
    <AdminDetailShell
      title="标准职位详情"
      activePage="data-positions"
      backPage="data-positions"
      backText="返回标准职位库"
    >
      {loading || error || !position ? (
        <DetailState loading={loading} error={error} emptyText="标准职位不存在" />
      ) : (
        <>
          <div className="admin-card">
            <div className="ac-title row" style={{ justifyContent: 'space-between' }}>
              <span>标准职位详情</span>
              <div className="row" style={{ gap: 8, marginLeft: 'auto' }}>
                <button type="button" className="a-btn sm" onClick={() => navigate('/admin', { state: { page: 'data-positions' } })}>返回列表</button>
              </div>
            </div>
            <div className="admin-info-grid">
              <div className="info-item"><span className="label">ID</span><span className="value">#{position.id}</span></div>
              <div className="info-item"><span className="label">标准名称</span><span className="value">{position.name}</span></div>
              <div className="info-item"><span className="label">分类</span><span className="value">{position.category}</span></div>
              <div className="info-item"><span className="label">状态</span><BaseDataStatusTag status={position.status} /></div>
              <div className="info-item"><span className="label">创建人</span><span className="value">{position.created_by || '-'}</span></div>
              <div className="info-item"><span className="label">更新人</span><span className="value">{position.updated_by || '-'}</span></div>
              <div className="info-item"><span className="label">创建时间</span><span className="value">{formatAdminDate(position.created_at)}</span></div>
              <div className="info-item"><span className="label">更新时间</span><span className="value">{formatAdminDate(position.updated_at)}</span></div>
            </div>
          </div>

          <div className="admin-card">
            <div className="ac-title">别名与说明</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <div className="tiny muted" style={{ marginBottom: 8 }}>别名</div>
                {(position.aliases || []).length > 0 ? position.aliases.map(alias => (
                  <span key={alias} className="a-tag blue" style={{ marginRight: 8, marginBottom: 6 }}>{alias}</span>
                )) : <span className="tiny muted">暂无别名</span>}
              </div>
              <div>
                <div className="tiny muted" style={{ marginBottom: 8 }}>说明</div>
                <div style={{ lineHeight: 1.7, color: 'var(--a-text)' }}>{position.description || '-'}</div>
              </div>
            </div>
          </div>

          <BaseDataDetailLogs logs={logs} />
        </>
      )}
    </AdminDetailShell>
  )
}

export function AdminTagLibraryList() {
  return (
    <AdminDetailShell
      title="标签库"
      activePage="data-tags"
      backPage="data-overview"
      backText="返回基础数据概览"
    >
      <BaseData section="tags" />
    </AdminDetailShell>
  )
}

export function AdminTagLibraryItemDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tag, setTag] = useState(null)
  const [parent, setParent] = useState(null)
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        setLoading(true)
        const detail = await getTagLibraryItem(id)
        let parentDetail = null
        if (detail.parent_id) {
          try {
            parentDetail = await getTagLibraryItem(detail.parent_id)
          } catch {
            parentDetail = null
          }
        }
        const logData = await listBaseDataOperationLogs({ resource_type: 'tag', resource_id: id, limit: 10 })
        if (!alive) return
        setTag(detail)
        setParent(parentDetail)
        setLogs(logData.items || [])
        setError('')
      } catch (err) {
        if (!alive) return
        setTag(null)
        setParent(null)
        setLogs([])
        setError(err.message || '标签详情加载失败')
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => { alive = false }
  }, [id])

  return (
    <AdminDetailShell
      title="标签详情"
      activePage="data-tags"
      backPath="/admin/tags"
      backText="返回标签库"
    >
      {loading || error || !tag ? (
        <DetailState loading={loading} error={error} emptyText="标签不存在" />
      ) : (
        <>
          <div className="admin-card">
            <div className="ac-title row" style={{ justifyContent: 'space-between' }}>
              <span>标签详情</span>
              <div className="row" style={{ gap: 8, marginLeft: 'auto' }}>
                <button type="button" className="a-btn sm" onClick={() => navigate('/admin/tags')}>返回列表</button>
              </div>
            </div>
            <div className="admin-info-grid">
              <div className="info-item"><span className="label">ID</span><span className="value">#{tag.id}</span></div>
              <div className="info-item"><span className="label">标签名称</span><span className="value">{tag.name}</span></div>
              <div className="info-item"><span className="label">分类</span><span className="value">{tag.category}</span></div>
              <div className="info-item"><span className="label">父级</span><span className="value">{parent?.name || tag.parent_id || '-'}</span></div>
              <div className="info-item">
                <span className="label">颜色</span>
                <span className="value">
                  {tag.color ? (
                    <span className="row" style={{ gap: 8 }}>
                      <span style={{ width: 16, height: 16, borderRadius: 4, background: tag.color, display: 'inline-block' }} />
                      {tag.color}
                    </span>
                  ) : '-'}
                </span>
              </div>
              <div className="info-item"><span className="label">排序</span><span className="value">{tag.sort_order}</span></div>
              <div className="info-item"><span className="label">状态</span><BaseDataStatusTag status={tag.status} /></div>
              <div className="info-item"><span className="label">创建人</span><span className="value">{tag.created_by || '-'}</span></div>
              <div className="info-item"><span className="label">更新人</span><span className="value">{tag.updated_by || '-'}</span></div>
              <div className="info-item"><span className="label">创建时间</span><span className="value">{formatAdminDate(tag.created_at)}</span></div>
              <div className="info-item"><span className="label">更新时间</span><span className="value">{formatAdminDate(tag.updated_at)}</span></div>
            </div>
          </div>

          <div className="admin-card">
            <div className="ac-title">说明</div>
            <div style={{ lineHeight: 1.7, color: 'var(--a-text)' }}>{tag.description || '-'}</div>
          </div>

          <BaseDataDetailLogs logs={logs} />
        </>
      )}
    </AdminDetailShell>
  )
}
