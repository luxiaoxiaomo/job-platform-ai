import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar } from '../components/ui.jsx'
import { recruiterNotifications, notificationTypes } from '../mock/data.js'
import { RecruiterBottomNav } from './RecruiterBottomNav.jsx'

export default function RecruiterNotifications() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState(recruiterNotifications)
  const unreadCount = notifications.filter(n => !n.read).length

  const markAllRead = () => {
    setNotifications(ns => ns.map(n => ({ ...n, read: true })))
  }

  const markRead = (id) => {
    setNotifications(ns => ns.map(n => n.id === id ? { ...n, read: true } : n))
  }

  const handleClick = (n) => {
    markRead(n.id)
    // 根据通知类型跳转
    if (n.type === 'application' || n.type === 'message') {
      navigate('/recruiter/talent')
    } else if (n.type === 'review') {
      navigate('/recruiter/jobs')
    } else if (n.type === 'system' || n.type === 'reminder') {
      navigate('/recruiter/stats')
    }
  }

  return (<>
    <NavBar title="通知中心" />
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
        {notifications.map(n => {
          const typeInfo = notificationTypes[n.type]
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
    <RecruiterBottomNav />
  </>)
}
