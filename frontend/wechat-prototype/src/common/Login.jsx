import React, { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { NavBar, FormCell, useToast, AIBadge } from '../components/ui.jsx'
import { login } from '../services/index.js'

/**
 * 通用登录页面
 */
export function Login() {
  const navigate = useNavigate()
  const toast = useToast()
  const [searchParams] = useSearchParams()
  const role = searchParams.get('role') || 'seeker'

  const [form, setForm] = useState({
    phone: '',
    password: '',
  })

  const [loading, setLoading] = useState(false)

  // 提交登录
  const handleSubmit = async () => {
    if (!form.phone || !form.password) {
      toast('请填写手机号和密码')
      return
    }

    if (!/^1[3-9]\d{9}$/.test(form.phone)) {
      toast('手机号格式不正确')
      return
    }

    try {
      setLoading(true)

      const response = await login(form.phone, form.password)

      toast('登录成功', '🎉')

      // 根据用户角色跳转
      setTimeout(() => {
        if (response.user.role === 'seeker') {
          navigate('/seeker/home')
        } else if (response.user.role === 'recruiter') {
          navigate('/recruiter/jobs')
        } else if (response.user.role === 'admin') {
          navigate('/admin')
        }
      }, 500)
    } catch (error) {
      toast(error.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <NavBar title="登录" onBack={() => navigate('/')} />
      <div className="page" style={{ paddingBottom: 90 }}>
        <div className="pad center" style={{ background: '#fff', paddingTop: 40, paddingBottom: 40 }}>
          <div style={{
            width: 80,
            height: 80,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #07C160 0%, #06AD56 100%)',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 36
          }}>
            💼
          </div>
          <div style={{ fontWeight: 600, fontSize: 20, marginTop: 16 }}>
            空岗对接平台
          </div>
          <div className="tiny muted" style={{ marginTop: 6 }}>
            AI增强 · 隐私保护
          </div>
        </div>

        <div className="cell-group-title">登录信息</div>
        <div className="cell-group">
          <FormCell label="手机号" req>
            <input
              type="tel"
              value={form.phone}
              placeholder="请输入手机号"
              maxLength={11}
              onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
              onKeyPress={e => e.key === 'Enter' && handleSubmit()}
            />
          </FormCell>

          <FormCell label="密码" req>
            <input
              type="password"
              value={form.password}
              placeholder="请输入密码"
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              onKeyPress={e => e.key === 'Enter' && handleSubmit()}
            />
          </FormCell>
        </div>

        {import.meta.env.VITE_USE_MOCK === 'false' && (
          <div className="ai-tip padx">
            <AIBadge soft>真实API</AIBadge>
            <span style={{ marginLeft: 6 }}>当前连接真实后端服务</span>
          </div>
        )}
      </div>

      <div className="page-foot">
        <button
          className={`btn ${loading ? 'btn-disabled' : 'btn-primary'}`}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? '登录中...' : '登录'}
        </button>
        <div className="center" style={{ marginTop: 12 }}>
          <span className="tiny muted">还没有账号？</span>
          <span
            className="tiny"
            style={{ color: 'var(--wx-green)', marginLeft: 4, cursor: 'pointer' }}
            onClick={() => navigate(`/register?role=${role}`)}
          >
            立即注册
          </span>
        </div>
      </div>
    </>
  )
}
