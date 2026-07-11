import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { NavBar, AIBadge, AICard, useToast } from '../components/ui.jsx'
import { RecruiterBottomNav } from './RecruiterBottomNav.jsx'
import { getMyJobVisitors } from '../services/index.js'

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function avatarColor(id) {
  const colors = ['#07C160', '#10AEFF', '#FA9D3B', '#7C5CFC', '#FF6B6B', '#36C5C5']
  return colors[Number(id || 0) % colors.length]
}

export function RecruiterVisitors() {
  const { jobId } = useParams()
  const toast = useToast()
  const [sort, setSort] = useState('intent')
  const [selected, setSelected] = useState(new Set())
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    setLoading(true)
    getMyJobVisitors(jobId, { sort, limit: 100 })
      .then(result => {
        if (!alive) return
        setData(result)
        setError('')
      })
      .catch(err => {
        if (!alive) return
        setData(null)
        setError(err.message || '访客数据加载失败')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })

    return () => { alive = false }
  }, [jobId, sort])

  const visitors = data?.items || []
  const highIntentCount = useMemo(() => visitors.filter(item => item.high_intent).length, [visitors])
  const conversationCount = useMemo(() => visitors.filter(item => item.has_conversation).length, [visitors])

  const toggle = (id) => {
    setSelected(current => {
      const next = new Set(current)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const inviteSelected = () => {
    const count = selected.size || visitors.length
    if (count === 0) {
      toast('暂无可邀请访客')
      return
    }
    toast(`已标记 ${count} 位访客为待跟进`)
  }

  return (
    <>
      <NavBar title="访客穿透" />
      <div className="page has-tabbar">
        <div style={{ background: '#fff', padding: '12px 16px', borderBottom: '0.5px solid var(--wx-line-light)' }}>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>
            {loading ? '加载岗位访客...' : data?.job_title || `岗位 #${jobId}`}
          </div>
          <div className="row gap12 tiny muted">
            <span>{loading ? '...' : data?.total_views || 0} 次浏览</span>
            <span>{loading ? '...' : data?.unique_visitors || 0} 位访客</span>
            <span>{loading ? '...' : conversationCount} 位已咨询</span>
          </div>
        </div>

        <div className="row" style={{ background: '#fff', padding: 16, gap: 0, borderBottom: '0.5px solid var(--wx-line-light)' }}>
          {[
            ['总浏览', loading ? '...' : data?.total_views || 0],
            ['独立访客', loading ? '...' : data?.unique_visitors || 0],
            ['高意向', loading ? '...' : highIntentCount],
            ['已咨询', loading ? '...' : conversationCount],
          ].map(([label, value]) => (
            <div key={label} className="grow center">
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--wx-blue)' }}>{value}</div>
              <div className="tiny muted" style={{ marginTop: 2 }}>{label}</div>
            </div>
          ))}
        </div>

        <div className="row between" style={{ background: '#fff', padding: '8px 16px', borderBottom: '0.5px solid var(--wx-line-light)' }}>
          <div className="row gap6">
            {[
              { key: 'intent', label: '按意向' },
              { key: 'views', label: '按次数' },
              { key: 'time', label: '按最近' },
            ].map(item => (
              <span
                key={item.key}
                className={`tag ${sort === item.key ? 'tag-green' : 'tag-gray'}`}
                style={{ cursor: 'pointer', fontSize: 12 }}
                onClick={() => setSort(item.key)}
              >
                {item.label}
              </span>
            ))}
          </div>
          <span
            className="tiny"
            style={{ color: 'var(--wx-green-dark)', cursor: 'pointer' }}
            onClick={() => setSelected(new Set(visitors.map(item => item.seeker_id)))}
          >
            全选
          </span>
        </div>

        {error && (
          <div style={{ margin: '12px 16px', padding: 12, borderRadius: 8, background: '#FFF5F5', color: 'var(--wx-red)', fontSize: 13 }}>
            {error}
          </div>
        )}

        {loading && (
          <div className="center muted" style={{ padding: '48px 0', fontSize: 13 }}>正在读取真实访客数据...</div>
        )}

        {!loading && visitors.length === 0 && !error && (
          <div className="empty" style={{ paddingTop: 80 }}>
            <span className="tiny muted">暂无已登录求职者访客。匿名浏览只计入总浏览，不进入访客名单。</span>
          </div>
        )}

        {!loading && visitors.length > 0 && (
          <div className="cell-group" style={{ marginTop: 0 }}>
            {visitors.map(visitor => (
              <div key={visitor.seeker_id} className="cell" style={{ alignItems: 'flex-start', padding: '12px 16px' }}>
                <span
                  style={{
                    marginRight: 10,
                    fontSize: 18,
                    color: selected.has(visitor.seeker_id) ? 'var(--wx-green)' : 'var(--wx-text-light)',
                    flexShrink: 0,
                    cursor: 'pointer',
                  }}
                  onClick={() => toggle(visitor.seeker_id)}
                >
                  {selected.has(visitor.seeker_id) ? '●' : '○'}
                </span>
                <span
                  className="avatar"
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 8,
                    background: avatarColor(visitor.seeker_id),
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 15,
                    fontWeight: 600,
                    marginRight: 10,
                    flexShrink: 0,
                  }}
                >
                  {(visitor.seeker_display_name || '?')[0]}
                </span>
                <div className="grow" style={{ overflow: 'hidden' }}>
                  <div className="row between">
                    <span style={{ fontWeight: 500 }}>{visitor.seeker_display_name}</span>
                    <span className={visitor.high_intent ? 'tag tag-green' : 'tag tag-gray'} style={{ fontSize: 12 }}>
                      意向 {visitor.intent_score}
                    </span>
                  </div>
                  <div className="row gap6" style={{ marginTop: 4, flexWrap: 'wrap' }}>
                    {(visitor.tags || []).map(tag => (
                      <span key={tag} className={tag === '高意向' ? 'tag tag-green' : 'tag tag-gray'} style={{ fontSize: 10, padding: '1px 6px' }}>
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="row between tiny muted" style={{ marginTop: 4 }}>
                    <span>浏览 {visitor.view_count} 次 · 最近 {formatDateTime(visitor.last_viewed_at)}</span>
                    <span>{visitor.has_application ? '已投递' : visitor.has_conversation ? '已咨询' : '未互动'}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <AICard title="AI 访客洞察" tip="基于真实访问、咨询和投递行为计算">
          {visitors.length > 0
            ? `当前岗位有 ${data?.unique_visitors || 0} 位已登录访客，其中 ${highIntentCount} 位为高意向，${conversationCount} 位已发起咨询。优先跟进多次浏览、已咨询或已投递的人。`
            : '当前还没有可穿透到人的访客记录。求职者登录后打开岗位详情，会自动进入这里。'}
        </AICard>
      </div>

      <div className="page-foot">
        <button className="btn btn-primary" onClick={inviteSelected}>
          标记 {selected.size || visitors.length} 位待跟进
        </button>
      </div>
      <RecruiterBottomNav />
    </>
  )
}
