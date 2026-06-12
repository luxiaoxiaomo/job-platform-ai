import React, { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { NavBar, FormCell, useToast, AIBadge } from '../components/ui.jsx'
import { sendVerificationCode, register } from '../services/index.js'

/**
 * 通用注册页面
 * 支持应聘者和招聘者注册
 */
export function Register() {
  const navigate = useNavigate()
  const toast = useToast()
  const [searchParams] = useSearchParams()
  const role = searchParams.get('role') || 'seeker' // seeker | recruiter

  const [form, setForm] = useState({
    phone: '',
    password: '',
    display_name: '',
    verification_code: '',
  })

  const [codeSent, setCodeSent] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const [loading, setLoading] = useState(false)

  // 发送验证码
  const handleSendCode = async () => {
    if (!form.phone) {
      toast('请输入手机号')
      return
    }

    if (!/^1[3-9]\d{9}$/.test(form.phone)) {
      toast('手机号格式不正确')
      return
    }

    if (countdown > 0) return

    try {
      setLoading(true)
      const response = await sendVerificationCode(form.phone)

      setCodeSent(true)
      setCountdown(60)

      // 倒计时
      const timer = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer)
            return 0
          }
          return prev - 1
        })
      }, 1000)

      // 开发环境显示验证码
      if (response.code) {
        toast(`验证码：${response.code}`, '✓')
      } else {
        toast('验证码已发送', '✓')
      }
    } catch (error) {
      toast(error.message || '发送失败')
    } finally {
      setLoading(false)
    }
  }

  // 提交注册
  const handleSubmit = async () => {
    // 验证
    if (!form.phone || !form.password || !form.display_name || !form.verification_code) {
      toast('请填写完整信息')
      return
    }

    if (!/^1[3-9]\d{9}$/.test(form.phone)) {
      toast('手机号格式不正确')
      return
    }

    if (form.password.length < 6) {
      toast('密码至少6位')
      return
    }

    try {
      setLoading(true)

      await register({
        phone: form.phone,
        password: form.password,
        display_name: form.display_name,
        role: role,
        verification_code: form.verification_code,
      })

      toast('注册成功', '🎉')

      // 跳转到对应角色首页
      setTimeout(() => {
        if (role === 'seeker') {
          navigate('/seeker/home')
        } else {
          navigate('/recruiter/register')
        }
      }, 800)
    } catch (error) {
      toast(error.message || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <NavBar title={role === 'seeker' ? '应聘者注册' : '招聘者注册'} onBack={() => navigate('/')} />
      <div className="page" style={{ paddingBottom: 90 }}>
        <div className="pad center" style={{ background: '#fff' }}>
          <div style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: 'var(--wx-green-bg)',
            margin: '12px auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 30
          }}>
            {role === 'seeker' ? '💼' : '🏢'}
          </div>
          <div style={{ fontWeight: 600, fontSize: 17 }}>
            {role === 'seeker' ? '应聘者注册' : '企业招聘者注册'}
          </div>
          <div className="tiny muted" style={{ marginTop: 4 }}>
            手机号注册，安全快捷
          </div>
        </div>

        <div className="cell-group-title">基本信息</div>
        <div className="cell-group">
          <FormCell label="手机号" req>
            <input
              type="tel"
              value={form.phone}
              placeholder="请输入手机号"
              maxLength={11}
              onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
            />
          </FormCell>

          <FormCell label="验证码" req>
            <input
              type="text"
              value={form.verification_code}
              placeholder="请输入验证码"
              maxLength={6}
              onChange={e => setForm(f => ({ ...f, verification_code: e.target.value }))}
              style={{ flex: 1 }}
            />
            <button
              className={`btn btn-sm ${countdown > 0 ? 'btn-disabled' : 'btn-default'}`}
              onClick={handleSendCode}
              disabled={countdown > 0 || loading}
              style={{ marginLeft: 8, minWidth: 90 }}
            >
              {countdown > 0 ? `${countdown}秒` : codeSent ? '重新发送' : '发送验证码'}
            </button>
          </FormCell>

          <FormCell label="密码" req>
            <input
              type="password"
              value={form.password}
              placeholder="至少6位密码"
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
            />
          </FormCell>

          <FormCell label="显示名称" req>
            <input
              type="text"
              value={form.display_name}
              placeholder={role === 'seeker' ? '您的姓名或昵称' : '企业名称或昵称'}
              onChange={e => setForm(f => ({ ...f, display_name: e.target.value }))}
            />
          </FormCell>
        </div>

        {import.meta.env.VITE_USE_MOCK === 'false' && (
          <div className="ai-tip padx">
            <AIBadge soft>真实API</AIBadge>
            <span style={{ marginLeft: 6 }}>当前连接真实后端服务</span>
          </div>
        )}

        <div className="padx" style={{ marginTop: 16 }}>
          <div className="tiny muted center">
            注册即表示同意《用户协议》和《隐私政策》
          </div>
        </div>
      </div>

      <div className="page-foot">
        <button
          className={`btn ${loading ? 'btn-disabled' : 'btn-primary'}`}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? '注册中...' : '注册'}
        </button>
        <div className="center" style={{ marginTop: 12 }}>
          <span className="tiny muted">已有账号？</span>
          <span
            className="tiny"
            style={{ color: 'var(--wx-green)', marginLeft: 4, cursor: 'pointer' }}
            onClick={() => navigate(`/login?role=${role}`)}
          >
            立即登录
          </span>
        </div>
      </div>
    </>
  )
}
