import React, { createContext, useContext, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

/* ============ Toast 全局 ============ */
const ToastCtx = createContext(() => {})
export const useToast = () => useContext(ToastCtx)

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null)
  const show = useCallback((text, icon) => {
    setToast({ text, icon })
    setTimeout(() => setToast(null), 1600)
  }, [])
  return (
    <ToastCtx.Provider value={show}>
      {children}
      {toast && (
        <div className="toast-mask">
          <div className="toast">
            {toast.icon && <div className="toast-icon">{toast.icon}</div>}
            <div>{toast.text}</div>
          </div>
        </div>
      )}
    </ToastCtx.Provider>
  )
}

/* ============ 手机壳 ============ */
export function Phone({ label, navBg, children }) {
  return (
    <div>
      <div className="phone" style={navBg ? { '--nav-bg': navBg } : undefined}>
        <StatusBar />
        {children}
      </div>
      {label && <div className="phone-label">{label}</div>}
    </div>
  )
}

export function StatusBar() {
  return (
    <div className="statusbar">
      <span>9:41</span>
      <span className="sb-icons">
        <span>●●●</span>
        <span>WiFi</span>
        <span>100%</span>
      </span>
    </div>
  )
}

/* ============ 导航栏 ============ */
export function NavBar({ title, onBack, right, back = true }) {
  const navigate = useNavigate()
  const handleBack = onBack || (() => navigate(-1))
  return (
    <div className="navbar">
      {back && <div className="nav-back" onClick={handleBack}>‹</div>}
      <div className="nav-title">{title}</div>
      {right && <div className="nav-right">{right}</div>}
    </div>
  )
}

/* ============ 底部 TabBar ============ */
export function TabBar({ tabs, active, onChange }) {
  return (
    <div className="tabbar">
      {tabs.map(t => (
        <div key={t.key} className={`tab ${active === t.key ? 'active' : ''}`} onClick={() => onChange(t.key)}>
          <span className="ti">{t.icon}</span>
          {t.badge ? <i className="tab-badge">{t.badge}</i> : null}
          <span>{t.label}</span>
        </div>
      ))}
    </div>
  )
}

/* ============ Cell 列表 ============ */
export function CellGroup({ title, inset, children }) {
  return (
    <>
      {title && <div className="cell-group-title">{title}</div>}
      <div className={`cell-group ${inset ? 'inset' : ''}`}>{children}</div>
    </>
  )
}

export function Cell({ icon, iconBg, label, value, valuePlaceholder, ft, link, onClick, arrow = true }) {
  return (
    <div className={`cell ${link ? 'link' : ''}`} onClick={onClick}>
      {icon && <span className="cell-icon" style={iconBg ? { background: iconBg } : undefined}>{icon}</span>}
      {label && <span className="cell-label">{label}</span>}
      <span className={`cell-value ${valuePlaceholder ? 'placeholder' : ''}`}>{value || valuePlaceholder}</span>
      {ft && <span className="cell-ft">{ft}</span>}
      {link && arrow && <span className="cell-arrow">›</span>}
    </div>
  )
}

/* ============ 表单 Cell ============ */
export function FormCell({ label, req, children }) {
  return (
    <div className="form-cell">
      <span className={`fc-label ${req ? 'req' : ''}`}>{label}</span>
      <div className="fc-body">{children}</div>
    </div>
  )
}

/* ============ AI 元素 ============ */
export function AIBadge({ children = 'AI', soft }) {
  return <span className={`ai-badge ${soft ? 'soft' : ''}`}>⚡{children}</span>
}

export function AIButton({ children, onClick, loading }) {
  return (
    <button className={`ai-btn ${loading ? 'loading' : ''}`} onClick={onClick} disabled={loading}>
      {loading ? <span className="spin" /> : '⚡'} {children}
    </button>
  )
}

export function AICard({ title, children, tip }) {
  return (
    <div className="ai-card">
      <div className="ai-card-hd">⚡ {title}</div>
      <div className="ai-card-bd">{children}</div>
      {tip && <div className="ai-tip">{tip}</div>}
    </div>
  )
}

/* ============ 标签 / 状态 ============ */
export function EmotionTag({ level }) {
  const map = { high: ['高意向', 'high'], medium: ['一般', 'medium'], low: ['仅咨询', 'low'] }
  const [text, cls] = map[level] || map.medium
  return <span className={`emotion ${cls}`}>● {text}</span>
}

export function StatusBadge({ status }) {
  const map = { online: '招聘中', pending: '审核中', closed: '已下架' }
  return <span className={`status-badge ${status}`}><span className="sb-dot" />{map[status] || status}</span>
}

/* ============ 开关 ============ */
export function Switch({ on, onClick }) {
  return <div className={`switch ${on ? 'on' : ''}`} onClick={onClick}><span className="knob" /></div>
}

/* ============ 底部弹层 ============ */
export function Sheet({ title, onClose, children }) {
  return (
    <div className="sheet-mask" onClick={onClose}>
      <div className="sheet" onClick={e => e.stopPropagation()}>
        {title && <div className="sheet-hd">{title}</div>}
        <div className="sheet-body">{children}</div>
      </div>
    </div>
  )
}
