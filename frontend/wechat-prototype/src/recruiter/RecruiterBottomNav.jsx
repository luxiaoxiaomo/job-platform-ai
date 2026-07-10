import React, { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { TabBar } from '../components/ui.jsx'
import { listMyConversations } from '../services/index.js'

/* ============ 招聘端底部导航（可复用） ============ */
export function RecruiterBottomNav() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    let alive = true
    listMyConversations({ limit: 100 })
      .then(data => {
        if (!alive) return
        setUnread((data.items || []).reduce((sum, item) => sum + (item.latest_message ? 1 : 0), 0))
      })
      .catch(() => {
        if (alive) setUnread(0)
      })
    return () => { alive = false }
  }, [])

  // 根据 URL 判断当前活跃 tab
  let active = 'jobs'
  if (pathname.startsWith('/recruiter/talent')) active = 'talent'
  else if (pathname.startsWith('/recruiter/chat')) active = 'messages'
  else if (pathname.startsWith('/recruiter/job') || pathname.startsWith('/recruiter/stats') || pathname.startsWith('/recruiter/candidate')) active = 'jobs'

  const tabs = [
    { key: 'jobs', label: '岗位', icon: '📋' },
    { key: 'talent', label: '人才', icon: '👥' },
    { key: 'messages', label: '消息', icon: '💬', badge: unread || null },
    { key: 'profile', label: '我的', icon: '👤' },
  ]

  const onChange = (key) => {
    if (key === 'jobs') navigate('/recruiter/jobs')
    if (key === 'talent') navigate('/recruiter/talent')
    if (key === 'messages') navigate('/recruiter/jobs?tab=messages')
    if (key === 'profile') navigate('/recruiter/jobs?tab=profile')
  }

  return <TabBar tabs={tabs} active={active} onChange={onChange} />
}
