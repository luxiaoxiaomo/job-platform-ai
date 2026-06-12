import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, FormCell, useToast, AIBadge } from '../components/ui.jsx'
import { getCurrentUserInfo, updateCurrentUser, getCurrentUser } from '../services/index.js'

/**
 * 用户信息编辑页面（通用）
 */
export function UserProfile() {
  const navigate = useNavigate()
  const toast = useToast()

  const [user, setUser] = useState(null)
  const [form, setForm] = useState({
    display_name: '',
    avatar_url: '',
  })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  // 加载用户信息
  useEffect(() => {
    loadUserInfo()
  }, [])

  const loadUserInfo = async () => {
    try {
      setLoading(true)

      // 先从localStorage获取
      const cachedUser = getCurrentUser()
      if (cachedUser) {
        setUser(cachedUser)
        setForm({
          display_name: cachedUser.display_name || '',
          avatar_url: cachedUser.avatar_url || '',
        })
      }

      // 再从API刷新
      const freshUser = await getCurrentUserInfo()
      setUser(freshUser)
      setForm({
        display_name: freshUser.display_name || '',
        avatar_url: freshUser.avatar_url || '',
      })
    } catch (error) {
      console.error('加载用户信息失败:', error)
      toast(error.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 保存修改
  const handleSave = async () => {
    if (!form.display_name.trim()) {
      toast('请填写显示名称')
      return
    }

    try {
      setSaving(true)

      const updatedUser = await updateCurrentUser({
        display_name: form.display_name,
        avatar_url: form.avatar_url || undefined,
      })

      setUser(updatedUser)
      toast('保存成功', '✓')

      // 返回上一页
      setTimeout(() => {
        navigate(-1)
      }, 500)
    } catch (error) {
      toast(error.message || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <>
        <NavBar title="个人信息" onBack={() => navigate(-1)} />
        <div className="page center" style={{ paddingTop: 100 }}>
          <div className="spin" style={{ width: 32, height: 32 }} />
          <div className="tiny muted" style={{ marginTop: 12 }}>加载中...</div>
        </div>
      </>
    )
  }

  if (!user) {
    return (
      <>
        <NavBar title="个人信息" onBack={() => navigate(-1)} />
        <div className="page center" style={{ paddingTop: 100 }}>
          <div className="tiny muted">未登录</div>
          <button
            className="btn btn-primary btn-sm"
            style={{ marginTop: 16 }}
            onClick={() => navigate('/login')}
          >
            去登录
          </button>
        </div>
      </>
    )
  }

  return (
    <>
      <NavBar title="个人信息" onBack={() => navigate(-1)} />
      <div className="page" style={{ paddingBottom: 90 }}>
        {/* 头像 */}
        <div className="pad center" style={{ background: '#fff', paddingTop: 24, paddingBottom: 24 }}>
          <div style={{
            width: 80,
            height: 80,
            borderRadius: '50%',
            background: user.avatar_url ? `url(${user.avatar_url})` : 'var(--wx-green-bg)',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            color: 'var(--wx-green-dark)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 32,
            fontWeight: 700,
          }}>
            {!user.avatar_url && (user.display_name?.[0] || '用')}
          </div>
          <div className="tiny muted" style={{ marginTop: 8 }}>点击修改头像（暂未实现）</div>
        </div>

        {/* 基本信息 */}
        <div className="cell-group-title">基本信息</div>
        <div className="cell-group">
          <div className="cell">
            <span className="cell-label">手机号</span>
            <span className="cell-value">{user.phone || '未设置'}</span>
          </div>
          <div className="cell">
            <span className="cell-label">角色</span>
            <span className="cell-value">
              {user.role === 'seeker' ? '应聘者' : user.role === 'recruiter' ? '招聘者' : '管理员'}
            </span>
          </div>
          <div className="cell">
            <span className="cell-label">状态</span>
            <span className="cell-value">
              <span className={`tag ${user.status === 'active' ? 'tag-green' : 'tag-gray'}`}>
                {user.status === 'active' ? '正常' : user.status === 'inactive' ? '未激活' : '已封禁'}
              </span>
            </span>
          </div>
        </div>

        {/* 可编辑信息 */}
        <div className="cell-group-title">可编辑信息</div>
        <div className="cell-group">
          <FormCell label="显示名称" req>
            <input
              type="text"
              value={form.display_name}
              placeholder="请输入显示名称"
              onChange={e => setForm(f => ({ ...f, display_name: e.target.value }))}
            />
          </FormCell>

          <FormCell label="头像URL">
            <input
              type="text"
              value={form.avatar_url}
              placeholder="选填，头像图片URL"
              onChange={e => setForm(f => ({ ...f, avatar_url: e.target.value }))}
            />
          </FormCell>
        </div>

        {import.meta.env.VITE_USE_MOCK === 'false' && (
          <div className="ai-tip padx">
            <AIBadge soft>真实API</AIBadge>
            <span style={{ marginLeft: 6 }}>数据来自真实后端</span>
          </div>
        )}

        {/* 其他信息 */}
        <div className="cell-group-title">其他信息</div>
        <div className="cell-group">
          <div className="cell">
            <span className="cell-label">注册时间</span>
            <span className="cell-value tiny muted">
              {user.created_at ? new Date(user.created_at).toLocaleString('zh-CN') : '-'}
            </span>
          </div>
        </div>
      </div>

      <div className="page-foot">
        <button
          className={`btn ${saving ? 'btn-disabled' : 'btn-primary'}`}
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? '保存中...' : '保存修改'}
        </button>
      </div>
    </>
  )
}
