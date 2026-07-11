import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, HomeNavLink } from '../components/ui.jsx'
import { seekerNotifications, notificationTypes } from '../mock/data.js'
import { listMyNotifications, markAllNotificationsRead, markNotificationRead } from '../services/index.js'

const NOTIFICATION_READ_EVENT = 'seeker-notifications-read'

function mapNotification(item) {
  const payload = item.payload || {}
  return {
    id: item.id,
    type: item.type,
    title: item.title,
    detail: item.detail,
    time: item.created_at ? new Date(item.created_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '',
    read: item.read,
    action_url: item.action_url,
    subscription_id: payload.subscription_id,
    matched_job_ids: payload.matched_job_ids || [],
  }
}

export default function SeekerNotifications() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const unreadCount = notifications.filter(n => !n.read).length

  useEffect(() => {
    let alive = true
    setLoading(true)
    listMyNotifications({ limit: 50 })
      .then(data => {
        if (!alive) return
        setNotifications((data.items || []).map(mapNotification))
        setError('')
      })
      .catch(err => {
        if (!alive) return
        setNotifications(seekerNotifications)
        setError(err.message || '通知加载失败，已显示演示数据')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => { alive = false }
  }, [])

  const markAllRead = async () => {
    try {
      const result = await markAllNotificationsRead()
      setNotifications(ns => ns.map(n => ({ ...n, read: true })))
      window.dispatchEvent(new CustomEvent(NOTIFICATION_READ_EVENT, { detail: { unread_count: result.unread_count } }))
    } catch {
      setNotifications(ns => ns.map(n => ({ ...n, read: true })))
      window.dispatchEvent(new CustomEvent(NOTIFICATION_READ_EVENT, { detail: { unread_count: 0 } }))
    }
  }

  const markRead = async (id) => {
    const current = notifications.find(n => n.id === id)
    if (!current || current.read) return null
    setNotifications(ns => ns.map(n => n.id === id ? { ...n, read: true } : n))
    try {
      const result = await markNotificationRead(id)
      window.dispatchEvent(new CustomEvent(NOTIFICATION_READ_EVENT, { detail: { unread_count: result.unread_count } }))
      return result
    } catch {
      window.dispatchEvent(new CustomEvent(NOTIFICATION_READ_EVENT, { detail: { delta: -1 } }))
      return null
    }
  }

  const handleClick = async (n) => {
    await markRead(n.id)
    if (n.action_url) {
      navigate(n.action_url)
      return
    }
    // 根据通知类型跳转
    if (n.type === 'match') {
      const target = n.action_url || `/seeker/home?tab=subs${n.subscription_id ? `&subscriptionId=${n.subscription_id}` : ''}`
      navigate(target)
    } else if (n.type === 'message') {
      navigate('/seeker/chat/1')
    } else if (n.type === 'interview') {
      navigate('/seeker/interview-prep')
    } else if (n.type === 'system') {
      navigate('/seeker/profile/edit')
    } else if (n.type === 'review' || n.type === 'application_status') {
      navigate('/seeker/applications')
    }
  }

  return (<>
    <NavBar title="通知中心" right={<HomeNavLink />} />
    <div style={{ paddingBottom: 60 }}>
      <div className="row between" style={{ padding: '12px 16px', background: 'var(--wx-bg)', borderBottom: '1px solid var(--wx-line)' }}>
        <span className="tiny muted">
          {unreadCount > 0 ? `${unreadCount} 条未读` : '已读全部消息'}
        </span>
        {unreadCount > 0 && (
          <button className="btn-link tiny" onClick={markAllRead}>全部标为已读</button>
        )}
      </div>

      <div className="cell-group">
        {loading && (
          <div className="cell">
            <span className="grow tiny muted">正在加载通知...</span>
          </div>
        )}
        {!loading && error && (
          <div className="cell">
            <span className="grow tiny" style={{ color: 'var(--wx-orange)' }}>{error}</span>
          </div>
        )}
        {notifications.map(n => {
          const typeInfo = notificationTypes[n.type] || notificationTypes.system
          return (
            <div
              key={n.id}
              className="cell"
              onClick={() => handleClick(n)}
              style={{
                alignItems: 'flex-start',
                background: n.read ? 'white' : 'var(--wx-bg)',
                position: 'relative',
                paddingLeft: n.read ? 16 : 20
              }}
            >
              {!n.read && (
                <div style={{
                  position: 'absolute',
                  left: 8,
                  top: 24,
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: 'var(--wx-red)'
                }} />
              )}
              <div style={{ fontSize: 22, marginRight: 12, marginTop: 2 }}>{typeInfo.icon}</div>
              <div className="grow">
                <div className="row between">
                  <span style={{ fontWeight: n.read ? 400 : 600, fontSize: 14 }}>{n.title}</span>
                  <span className="tiny muted">{n.time}</span>
                </div>
                <div className="tiny muted" style={{ marginTop: 4, lineHeight: 1.5 }}>{n.detail}</div>
              </div>
            </div>
          )
        })}
      </div>

      {notifications.length === 0 && (
        <div className="empty" style={{ paddingTop: 100 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🔔</div>
          <div>暂无通知</div>
        </div>
      )}
    </div>
  </>)
}
