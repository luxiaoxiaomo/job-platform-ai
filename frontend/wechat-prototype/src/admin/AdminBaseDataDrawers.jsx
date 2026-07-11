import React, { useCallback, useEffect, useRef, useState } from 'react'
import {
  createStandardPosition,
  createTagLibraryItem,
  getStandardPosition,
  getTagLibraryItem,
  updateStandardPosition,
  updateTagLibraryItem,
} from '../services/index.js'
import {
  buildStandardPositionPayload,
  buildTagPayload,
  filterTagParentOptions,
  validateStandardPositionForm,
  validateTagForm,
} from './AdminBaseDataDrawerUtils.js'

const STANDARD_POSITION_DEFAULTS = {
  name: '',
  category: '',
  aliasesText: '',
  description: '',
  status: 'active',
}

const TAG_DEFAULTS = {
  name: '',
  category: '',
  parentId: '',
  color: '',
  description: '',
  sortOrder: 0,
  status: 'active',
}

function FormField({ label, required = false, error, children, className = '' }) {
  return (
    <label className={`admin-drawer-field ${className}`}>
      <span className="admin-drawer-label">{label}{required && <em>*</em>}</span>
      {children}
      {error && <span className="admin-drawer-field-error">{error}</span>}
    </label>
  )
}

function AdminBaseDataDrawer({
  open,
  title,
  dirty,
  loading,
  loadError,
  onRetry,
  saving,
  saveLabel,
  onSave,
  onClose,
  children,
}) {
  const requestClose = useCallback(() => {
    if (dirty && !window.confirm('当前修改尚未保存，确认关闭抽屉吗？')) return
    onClose()
  }, [dirty, onClose])

  useEffect(() => {
    if (!open) return undefined
    const handleKeyDown = event => {
      if (event.key === 'Escape') requestClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, requestClose])

  if (!open) return null

  return (
    <div
      className="admin-drawer-mask"
      onMouseDown={event => {
        if (event.target === event.currentTarget) requestClose()
      }}
    >
      <section className="admin-drawer" role="dialog" aria-modal="true" aria-label={title}>
        <header className="admin-drawer-head">
          <div>
            <div className="admin-drawer-title">{title}</div>
            <div className="admin-drawer-subtitle">保存后将自动刷新列表</div>
          </div>
          <button type="button" className="admin-drawer-close" onClick={requestClose} aria-label="关闭抽屉">×</button>
        </header>

        <div className="admin-drawer-body">
          {loading ? (
            <div className="admin-drawer-state">加载最新数据中...</div>
          ) : loadError ? (
            <div className="admin-drawer-state error">
              <div>{loadError}</div>
              <button type="button" className="a-btn sm" onClick={onRetry}>重试</button>
            </div>
          ) : children}
        </div>

        <footer className="admin-drawer-foot">
          <button type="button" className="a-btn" onClick={requestClose} disabled={saving}>取消</button>
          <button type="button" className="a-btn primary" onClick={onSave} disabled={loading || Boolean(loadError) || saving}>
            {saving ? '保存中...' : saveLabel}
          </button>
        </footer>
      </section>
    </div>
  )
}

export function StandardPositionDrawer({ open, mode, itemId, onClose, onSaved }) {
  const [form, setForm] = useState(STANDARD_POSITION_DEFAULTS)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)
  const initialValue = useRef(JSON.stringify(STANDARD_POSITION_DEFAULTS))

  useEffect(() => {
    if (!open) return undefined
    setErrors({})
    setSaveError('')
    if (mode !== 'edit') {
      const nextForm = { ...STANDARD_POSITION_DEFAULTS }
      setForm(nextForm)
      initialValue.current = JSON.stringify(nextForm)
      setLoading(false)
      setLoadError('')
      return undefined
    }

    let alive = true
    setLoading(true)
    setLoadError('')
    ;(async () => {
      try {
        const item = await getStandardPosition(itemId)
        if (!alive) return
        const nextForm = {
          name: item.name || '',
          category: item.category || '',
          aliasesText: (item.aliases || []).join(', '),
          description: item.description || '',
          status: item.status || 'active',
        }
        setForm(nextForm)
        initialValue.current = JSON.stringify(nextForm)
      } catch (error) {
        if (alive) setLoadError(error.message || '标准职位详情加载失败')
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => { alive = false }
  }, [open, mode, itemId, reloadKey])

  const updateField = (field, value) => {
    setForm(current => ({ ...current, [field]: value }))
    setErrors(current => ({ ...current, [field]: '' }))
    setSaveError('')
  }

  const save = async () => {
    const nextErrors = validateStandardPositionForm(form)
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      return
    }
    try {
      setSaving(true)
      setSaveError('')
      const payload = buildStandardPositionPayload(form)
      const saved = mode === 'edit'
        ? await updateStandardPosition(itemId, payload)
        : await createStandardPosition(payload)
      onSaved(saved, mode)
    } catch (error) {
      setSaveError(error.message || '保存标准职位失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <AdminBaseDataDrawer
      open={open}
      title={mode === 'edit' ? '编辑标准职位' : '新增标准职位'}
      dirty={!loading && JSON.stringify(form) !== initialValue.current}
      loading={loading}
      loadError={loadError}
      onRetry={() => setReloadKey(value => value + 1)}
      saving={saving}
      saveLabel={mode === 'edit' ? '保存修改' : '创建标准职位'}
      onSave={save}
      onClose={onClose}
    >
      <div className="admin-drawer-form">
        <FormField label="标准名称" required error={errors.name}>
          <input value={form.name} onChange={event => updateField('name', event.target.value)} placeholder="例如：Java 开发工程师" autoFocus />
        </FormField>
        <FormField label="分类" required error={errors.category}>
          <input value={form.category} onChange={event => updateField('category', event.target.value)} placeholder="例如：技术 / 研发" />
        </FormField>
        <FormField label="别名">
          <input value={form.aliasesText} onChange={event => updateField('aliasesText', event.target.value)} placeholder="多个别名使用逗号分隔" />
          <span className="admin-drawer-hint">别名用于 AI 职位名称标准化映射。</span>
        </FormField>
        <FormField label="说明">
          <textarea value={form.description} onChange={event => updateField('description', event.target.value)} placeholder="补充职位边界或使用说明" rows={5} />
        </FormField>
        <FormField label="状态" required>
          <select value={form.status} onChange={event => updateField('status', event.target.value)}>
            <option value="active">启用</option>
            <option value="inactive">停用</option>
          </select>
        </FormField>
        {saveError && <div className="admin-drawer-save-error">{saveError}</div>}
      </div>
    </AdminBaseDataDrawer>
  )
}

export function TagLibraryDrawer({ open, mode, itemId, tags, onClose, onSaved }) {
  const [form, setForm] = useState(TAG_DEFAULTS)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)
  const initialValue = useRef(JSON.stringify(TAG_DEFAULTS))

  useEffect(() => {
    if (!open) return undefined
    setErrors({})
    setSaveError('')
    if (mode !== 'edit') {
      const nextForm = { ...TAG_DEFAULTS }
      setForm(nextForm)
      initialValue.current = JSON.stringify(nextForm)
      setLoading(false)
      setLoadError('')
      return undefined
    }

    let alive = true
    setLoading(true)
    setLoadError('')
    ;(async () => {
      try {
        const item = await getTagLibraryItem(itemId)
        if (!alive) return
        const nextForm = {
          name: item.name || '',
          category: item.category || '',
          parentId: item.parent_id ? String(item.parent_id) : '',
          color: item.color || '',
          description: item.description || '',
          sortOrder: item.sort_order ?? 0,
          status: item.status || 'active',
        }
        setForm(nextForm)
        initialValue.current = JSON.stringify(nextForm)
      } catch (error) {
        if (alive) setLoadError(error.message || '标签详情加载失败')
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => { alive = false }
  }, [open, mode, itemId, reloadKey])

  const updateField = (field, value) => {
    setForm(current => ({ ...current, [field]: value }))
    setErrors(current => ({ ...current, [field]: '' }))
    setSaveError('')
  }

  const save = async () => {
    const nextErrors = validateTagForm(form)
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      return
    }
    try {
      setSaving(true)
      setSaveError('')
      const payload = buildTagPayload(form)
      const saved = mode === 'edit'
        ? await updateTagLibraryItem(itemId, payload)
        : await createTagLibraryItem(payload)
      onSaved(saved, mode)
    } catch (error) {
      setSaveError(error.message || '保存标签失败')
    } finally {
      setSaving(false)
    }
  }

  const parentOptions = filterTagParentOptions(tags || [], mode === 'edit' ? itemId : null)

  return (
    <AdminBaseDataDrawer
      open={open}
      title={mode === 'edit' ? '编辑标签' : '新增标签'}
      dirty={!loading && JSON.stringify(form) !== initialValue.current}
      loading={loading}
      loadError={loadError}
      onRetry={() => setReloadKey(value => value + 1)}
      saving={saving}
      saveLabel={mode === 'edit' ? '保存修改' : '创建标签'}
      onSave={save}
      onClose={onClose}
    >
      <div className="admin-drawer-form">
        <FormField label="标签名称" required error={errors.name}>
          <input value={form.name} onChange={event => updateField('name', event.target.value)} placeholder="例如：PeopleSoft" autoFocus />
        </FormField>
        <FormField label="分类" required error={errors.category}>
          <input value={form.category} onChange={event => updateField('category', event.target.value)} placeholder="例如：skill / industry" />
        </FormField>
        <FormField label="父级标签">
          <select value={form.parentId} onChange={event => updateField('parentId', event.target.value)}>
            <option value="">无父级</option>
            {parentOptions.map(tag => (
              <option key={tag.id} value={tag.id}>{tag.category} / {tag.name}</option>
            ))}
          </select>
        </FormField>
        <div className="admin-drawer-grid two">
          <FormField label="颜色">
            <div className="admin-color-field">
              <input type="color" value={form.color || '#2563eb'} onChange={event => updateField('color', event.target.value)} aria-label="选择标签颜色" />
              <input value={form.color} onChange={event => updateField('color', event.target.value)} placeholder="#2563eb" />
            </div>
          </FormField>
          <FormField label="排序" error={errors.sortOrder}>
            <input type="number" min="0" step="1" value={form.sortOrder} onChange={event => updateField('sortOrder', event.target.value)} />
          </FormField>
        </div>
        <FormField label="说明">
          <textarea value={form.description} onChange={event => updateField('description', event.target.value)} placeholder="补充标签含义或使用范围" rows={5} />
        </FormField>
        <FormField label="状态" required>
          <select value={form.status} onChange={event => updateField('status', event.target.value)}>
            <option value="active">启用</option>
            <option value="inactive">停用</option>
          </select>
        </FormField>
        {saveError && <div className="admin-drawer-save-error">{saveError}</div>}
      </div>
    </AdminBaseDataDrawer>
  )
}
