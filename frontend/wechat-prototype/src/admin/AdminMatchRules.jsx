import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useToast } from '../components/ui.jsx'
import {
  createMatchRuleConfigVersion,
  getCurrentUser,
  getMatchRuleConfig,
  logout,
} from '../services/index.js'
import '../styles/admin.css'

const STATUS_COLORS = {
  active: 'green',
  draft: 'gray',
  testing: 'blue',
  archived: 'orange',
}

const STATUS_LABELS = {
  active: '生效中',
  draft: '草稿',
  testing: '测试中',
  archived: '已归档',
}

function AdminShell({ title, activeNav = 'data', backText = '返回基础数据', onBack, children }) {
  const navigate = useNavigate()
  const currentUser = getCurrentUser()
  const adminName = currentUser?.display_name || currentUser?.phone || 'admin'

  const navItem = (key, icon, label) => (
    <div
      key={key}
      className={`nav-item ${activeNav === key ? 'active' : ''}`}
      onClick={() => navigate('/admin')}
    >
      <span className="ico">{icon}</span>
      {label}
    </div>
  )

  return (
    <div className="admin">
      <aside className="admin-side">
        <div className="admin-brand"><span className="dot" />岗位平台 · 运营后台</div>
        <nav className="admin-nav">
          {navItem('dash', '数', '数据概览')}
          {navItem('review', '审', '审核管理')}
          {navItem('users', '用', '用户管理')}
          {navItem('ai', '智', 'AI 监控')}
          {navItem('data', '资', '基础数据')}
        </nav>
        <div className="admin-side-foot" onClick={onBack || (() => navigate('/admin'))}>
          {backText}
        </div>
      </aside>

      <main className="admin-main">
        <header className="admin-topbar">
          <span className="at-title">{title}</span>
          <div className="at-right">
            <span className="admin-user-label">管理员 · {adminName}</span>
            <button type="button" className="admin-logout-btn" onClick={logout}>
              退出登录
            </button>
          </div>
        </header>
        <div className="admin-content">{children}</div>
      </main>
    </div>
  )
}

function RuleHeaderActions({ config, editable = false }) {
  const navigate = useNavigate()
  if (!config) return null

  return (
    <div style={{ display: 'flex', gap: 8 }}>
      {editable ? (
        <button
          type="button"
          className="a-btn sm primary"
          onClick={() => navigate(`/admin/match-rules/${config.id}/edit`)}
        >
          编辑配置
        </button>
      ) : (
        <button
          type="button"
          className="a-btn sm"
          disabled
          title="规则编辑功能将在后续版本开放"
          style={{ cursor: 'not-allowed', opacity: 0.5 }}
        >
          编辑配置
        </button>
      )}
    </div>
  )
}

function RuleDetailContent({ config, editable = false }) {
  const navigate = useNavigate()

  return (
    <>
      <div className="admin-card" style={{ marginBottom: 16 }}>
        <div className="ac-title row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ cursor: 'pointer', marginRight: 8 }} onClick={() => navigate('/admin')}>
              返回
            </span>
            {config.name}
          </div>
          <RuleHeaderActions config={config} editable={editable} />
        </div>
      </div>

      <div className="admin-card" style={{ marginBottom: 16 }}>
        <div className="ac-title">基础信息</div>
        <div style={{ padding: '16px 20px' }}>
          <div className="admin-info-grid">
            <div className="info-item"><span className="label">规则名称</span><span className="value">{config.name}</span></div>
            <div className="info-item"><span className="label">匹配策略</span><span className="value">{config.strategy}</span></div>
            <div className="info-item"><span className="label">应用范围</span><span className="value">{config.scope}</span></div>
            <div className="info-item"><span className="label">状态</span><span className={`a-tag ${STATUS_COLORS[config.status] || 'gray'}`}>{STATUS_LABELS[config.status] || config.status}</span></div>
            <div className="info-item"><span className="label">版本</span><span className="value">V{config.version}</span></div>
            <div className="info-item"><span className="label">更新时间</span><span className="value">{new Date(config.updated_at).toLocaleString('zh-CN')}</span></div>
            {config.effective_from ? <div className="info-item"><span className="label">生效时间</span><span className="value">{new Date(config.effective_from).toLocaleString('zh-CN')}</span></div> : null}
            {config.effective_to ? <div className="info-item"><span className="label">失效时间</span><span className="value">{new Date(config.effective_to).toLocaleString('zh-CN')}</span></div> : null}
          </div>
          {config.description ? (
            <div style={{ marginTop: 16, padding: '12px 16px', background: '#F7F8FA', borderRadius: 4, fontSize: 13, color: '#666' }}>
              {config.description}
            </div>
          ) : null}
        </div>
      </div>

      <div className="admin-card" style={{ marginBottom: 16 }}>
        <div className="ac-title">权重概览</div>
        <div style={{ padding: '16px 20px' }}>
          <div className="admin-info-grid">
            <div className="info-item"><span className="label">配置权重总和</span><span className="value">{config.configured_total_weight}</span></div>
            <div className="info-item"><span className="label">实际生效权重</span><span className="value">{config.effective_total_weight}</span></div>
            <div className="info-item"><span className="label">维度数量</span><span className="value">{config.dimensions?.length || 0} 个</span></div>
            <div className="info-item"><span className="label">启用维度</span><span className="value">{config.dimensions?.filter(item => item.enabled).length || 0} 个</span></div>
          </div>
        </div>
      </div>

      <div className="admin-card">
        <div className="ac-title">维度配置</div>
        <table className="admin-table">
          <thead>
            <tr>
              <th>维度</th>
              <th>Key</th>
              <th>状态</th>
              <th>配置权重</th>
              <th>生效权重</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            {config.dimensions?.map(item => (
              <tr key={item.key}>
                <td style={{ fontWeight: 500 }}>{item.label}</td>
                <td><code style={{ fontSize: 12, color: '#666' }}>{item.key}</code></td>
                <td><span className={`a-tag ${item.enabled ? 'pass' : 'gray'}`}>{item.enabled ? '启用' : '禁用'}</span></td>
                <td>{item.configured_weight || item.weight}%</td>
                <td>{item.effective_weight}%</td>
                <td>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>{item.description}</div>
                  <details style={{ fontSize: 12, color: '#999' }}>
                    <summary style={{ cursor: 'pointer', marginBottom: 4 }}>评分方法</summary>
                    <div style={{ paddingLeft: 12, marginTop: 4, lineHeight: 1.6 }}>{item.scoring_method}</div>
                  </details>
                  {item.logic && Object.keys(item.logic).length > 0 ? (
                    <details style={{ fontSize: 12, color: '#999', marginTop: 6 }}>
                      <summary style={{ cursor: 'pointer' }}>逻辑配置 [JSON]</summary>
                      <pre style={{ marginTop: 8, padding: 8, background: '#F7F8FA', borderRadius: 4, fontSize: 11, overflow: 'auto' }}>
                        {JSON.stringify(item.logic, null, 2)}
                      </pre>
                    </details>
                  ) : null}
                </td>
              </tr>
            ))}
            {!config.dimensions || config.dimensions.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', color: 'var(--a-text-2)', padding: 30 }}>
                  暂无维度配置
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </>
  )
}

export function AdminMatchRuleDetail() {
  const { id } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [config, setConfig] = useState(null)

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        setLoading(true)
        const data = await getMatchRuleConfig(id)
        if (!alive) return
        setConfig(data)
        setError('')
      } catch (err) {
        if (!alive) return
        setError(err.message || '规则配置加载失败')
      } finally {
        if (alive) setLoading(false)
      }
    })()

    return () => {
      alive = false
    }
  }, [id])

  return (
    <AdminShell title="人岗匹配规则详情">
      {loading ? <div className="admin-card"><div style={{ padding: 40, textAlign: 'center', color: 'var(--a-text-2)' }}>加载中...</div></div> : null}
      {!loading && (error || !config) ? (
        <div className="admin-card">
          <div style={{ padding: 40, textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>!</div>
            <div style={{ color: 'var(--a-text-2)', marginBottom: 20 }}>{error || '规则配置不存在'}</div>
          </div>
        </div>
      ) : null}
      {!loading && config ? <RuleDetailContent config={config} editable /> : null}
    </AdminShell>
  )
}

function buildFormState(config) {
  return {
    name: config.name,
    description: config.description || '',
    status: config.status || 'draft',
    scope: config.scope || 'global',
    dimensions: (config.dimensions || []).map(item => ({
      key: item.key,
      label: item.label,
      weight: item.configured_weight ?? item.weight ?? 0,
      enabled: !!item.enabled,
      description: item.description || '',
      scoring_method: item.scoring_method || '',
      logic: item.logic || {},
      sort_order: item.sort_order || 0,
    })),
  }
}

export function AdminMatchRuleEdit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [config, setConfig] = useState(null)
  const [form, setForm] = useState(null)
  const [logicDrafts, setLogicDrafts] = useState({})

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        setLoading(true)
        const data = await getMatchRuleConfig(id)
        if (!alive) return
        setConfig(data)
        setForm(buildFormState(data))
        setLogicDrafts(
          Object.fromEntries(
            (data.dimensions || []).map(item => [item.key, JSON.stringify(item.logic || {}, null, 2)])
          )
        )
        setError('')
      } catch (err) {
        if (!alive) return
        setError(err.message || '规则配置加载失败')
      } finally {
        if (alive) setLoading(false)
      }
    })()

    return () => {
      alive = false
    }
  }, [id])

  const enabledWeightTotal = useMemo(() => {
    if (!form?.dimensions) return 0
    return Number(
      form.dimensions
        .filter(item => item.enabled)
        .reduce((sum, item) => sum + Number(item.weight || 0), 0)
        .toFixed(2)
    )
  }, [form])

  const updateDimension = (key, patch) => {
    setForm(prev => ({
      ...prev,
      dimensions: prev.dimensions.map(item => (item.key === key ? { ...item, ...patch } : item)),
    }))
  }

  const updateLogicText = (key, value) => {
    setLogicDrafts(prev => ({ ...prev, [key]: value }))
    try {
      const parsed = JSON.parse(value || '{}')
      updateDimension(key, { logic: parsed })
    } catch {
      // JSON 未合法前只保留草稿文本
    }
  }

  const handleSave = async () => {
    if (!form) return

    if (!form.name.trim()) {
      toast('请填写规则名称')
      return
    }

    if (!form.dimensions.some(item => item.enabled && Number(item.weight) > 0)) {
      toast('至少保留一个启用且权重大于 0 的维度')
      return
    }

    for (const item of form.dimensions) {
      const draft = logicDrafts[item.key]
      try {
        JSON.parse(draft || '{}')
      } catch {
        toast(`维度 ${item.label} 的逻辑配置不是合法 JSON`)
        return
      }
    }

    try {
      setSaving(true)
      const payload = {
        name: form.name.trim(),
        description: form.description.trim(),
        status: form.status,
        scope: form.scope.trim() || 'global',
        dimensions: form.dimensions.map(item => ({
          key: item.key,
          label: item.label.trim(),
          weight: Number(item.weight || 0),
          enabled: !!item.enabled,
          description: item.description.trim(),
          scoring_method: item.scoring_method.trim(),
          logic: item.logic || {},
          sort_order: Number(item.sort_order || 0),
        })),
      }
      const result = await createMatchRuleConfigVersion(id, payload)
      toast('已生成新版本并保存', 'success')
      navigate(`/admin/match-rules/${result.config.id}`)
    } catch (err) {
      toast(err.message || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <AdminShell
      title="编辑人岗匹配规则"
      backText="返回规则详情"
      onBack={() => navigate(`/admin/match-rules/${id}`)}
    >
      {loading ? <div className="admin-card"><div style={{ padding: 40, textAlign: 'center', color: 'var(--a-text-2)' }}>加载中...</div></div> : null}
      {!loading && (error || !form || !config) ? (
        <div className="admin-card">
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--a-text-2)' }}>
            {error || '规则配置不存在'}
          </div>
        </div>
      ) : null}
      {!loading && form && config ? (
        <>
          <div className="admin-card" style={{ marginBottom: 16 }}>
            <div className="ac-title row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
              <div>基于 V{config.version} 生成新版本</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button type="button" className="a-btn sm" onClick={() => navigate(`/admin/match-rules/${id}`)}>
                  取消
                </button>
                <button
                  type="button"
                  className={`a-btn sm primary ${saving ? 'disabled' : ''}`}
                  disabled={saving}
                  onClick={handleSave}
                >
                  {saving ? '保存中...' : '保存为新版本'}
                </button>
              </div>
            </div>
            <div className="admin-form-grid">
              <label className="admin-field">
                <span>规则名称</span>
                <input value={form.name} onChange={e => setForm(prev => ({ ...prev, name: e.target.value }))} />
              </label>
              <label className="admin-field">
                <span>状态</span>
                <select value={form.status} onChange={e => setForm(prev => ({ ...prev, status: e.target.value }))}>
                  <option value="draft">草稿</option>
                  <option value="active">生效中</option>
                  <option value="testing">测试中</option>
                  <option value="archived">已归档</option>
                </select>
              </label>
              <label className="admin-field">
                <span>应用范围</span>
                <input value={form.scope} onChange={e => setForm(prev => ({ ...prev, scope: e.target.value }))} />
              </label>
              <div className="admin-field readonly">
                <span>启用维度配置权重总和</span>
                <strong>{enabledWeightTotal}</strong>
              </div>
            </div>
            <label className="admin-field" style={{ marginTop: 16 }}>
              <span>说明</span>
              <textarea
                value={form.description}
                onChange={e => setForm(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
              />
            </label>
          </div>

          <div className="admin-card">
            <div className="ac-title">维度编辑</div>
            <div className="admin-dimension-list">
              {form.dimensions.map(item => (
                <div key={item.key} className="admin-dimension-item">
                  <div className="admin-dimension-head">
                    <div>
                      <div className="admin-dimension-title">{item.label}</div>
                      <div className="admin-dimension-key">{item.key}</div>
                    </div>
                    <label className="admin-checkbox">
                      <input
                        type="checkbox"
                        checked={item.enabled}
                        onChange={e => updateDimension(item.key, { enabled: e.target.checked })}
                      />
                      启用
                    </label>
                  </div>
                  <div className="admin-form-grid compact">
                    <label className="admin-field">
                      <span>显示名称</span>
                      <input value={item.label} onChange={e => updateDimension(item.key, { label: e.target.value })} />
                    </label>
                    <label className="admin-field">
                      <span>配置权重</span>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.01"
                        value={item.weight}
                        onChange={e => updateDimension(item.key, { weight: e.target.value })}
                      />
                    </label>
                    <label className="admin-field">
                      <span>排序</span>
                      <input
                        type="number"
                        min="0"
                        step="1"
                        value={item.sort_order}
                        onChange={e => updateDimension(item.key, { sort_order: e.target.value })}
                      />
                    </label>
                  </div>
                  <label className="admin-field">
                    <span>维度说明</span>
                    <textarea rows={2} value={item.description} onChange={e => updateDimension(item.key, { description: e.target.value })} />
                  </label>
                  <label className="admin-field">
                    <span>评分方法</span>
                    <textarea rows={2} value={item.scoring_method} onChange={e => updateDimension(item.key, { scoring_method: e.target.value })} />
                  </label>
                  <details className="admin-logic-editor">
                    <summary>逻辑配置 [JSON]</summary>
                    <textarea rows={5} value={logicDrafts[item.key] || '{}'} onChange={e => updateLogicText(item.key, e.target.value)} />
                  </details>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : null}
    </AdminShell>
  )
}
