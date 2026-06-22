import React, { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, HomeNavLink, useToast } from '../components/ui.jsx'
import { pickColor } from '../mock/data.js'
import {
  getConversation,
  getReplySuggestions,
  replyConversation,
  requestContactExchange,
  reviewContactExchange,
} from '../services/index.js'

const exchangeButtonStyle = {
  color: 'var(--wx-blue)',
  borderColor: '#BEE3FA',
  background: '#EFF8FF',
}

const declineButtonStyle = {
  color: 'var(--wx-text-2)',
  borderColor: '#D8D8D8',
  background: '#FFFFFF',
}

function formatContact(contact) {
  return [
    contact.display_name,
    contact.company_name,
    contact.phone,
    contact.email,
    contact.wechat,
  ].filter(Boolean).join(' · ')
}

function ContactCard({ contacts, role }) {
  const peerRole = role === 'recruiter' ? 'seeker' : 'recruiter'
  const visibleContacts = (contacts || []).filter(contact => contact.role === peerRole)
  if (!visibleContacts.length) return null

  return (
    <div style={{ margin: '12px 16px', padding: '14px', background: 'linear-gradient(135deg,#ECF9F1,#E8F5FF)', borderRadius: 10, textAlign: 'center' }}>
      <div style={{ fontSize: 18, marginBottom: 6 }}>联系方式已开放</div>
      <div className="tiny muted" style={{ marginTop: 4, lineHeight: 1.8 }}>
        {visibleContacts.map(contact => (
          <div key={contact.user_id}>{formatContact(contact)}</div>
        ))}
      </div>
    </div>
  )
}

function ContactExchangeBar({ exchange, role, onRequest, onAccept, onDecline }) {
  if (!exchange) {
    return (
      <button className="ai-btn" style={exchangeButtonStyle} onClick={onRequest}>
        请求交换联系方式
      </button>
    )
  }

  if (exchange.status === 'accepted') {
    return <span className="ai-btn" style={{ color: 'var(--wx-green)', borderColor: '#BFEFD2', background: '#F0FFF6' }}>已交换联系方式</span>
  }

  if (exchange.status === 'declined') {
    return (
      <button className="ai-btn" style={exchangeButtonStyle} onClick={onRequest}>
        再次请求交换
      </button>
    )
  }

  if (exchange.requester_role === role) {
    return <span className="ai-btn" style={{ color: 'var(--wx-text-2)', borderColor: '#E5E5E5', background: '#F7F7F7' }}>等待对方同意</span>
  }

  return (
    <>
      <button className="ai-btn" style={exchangeButtonStyle} onClick={onAccept}>
        同意交换联系方式
      </button>
      <button className="ai-btn" style={declineButtonStyle} onClick={onDecline}>
        暂不同意
      </button>
    </>
  )
}

function RealConversationPage({ role, aiButtonLabel, onRightAction }) {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const inputRef = useRef(null)
  const [conversation, setConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAI, setShowAI] = useState(false)
  const [aiReplies, setAiReplies] = useState([])
  const [aiLoading, setAiLoading] = useState(false)
  const [aiError, setAiError] = useState('')
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)

  const loadConversation = useCallback((options = {}) => {
    const silent = Boolean(options.silent)
    if (!silent) setLoading(true)
    getConversation(id)
      .then(data => {
        setConversation(data)
        setMessages(data.messages || [])
      })
      .catch(error => {
        if (!silent) toast(error.message || '对话加载失败')
      })
      .finally(() => {
        if (!silent) setLoading(false)
      })
  }, [id, toast])

  useEffect(() => {
    loadConversation()
  }, [loadConversation])

  useEffect(() => {
    const refreshSilently = () => loadConversation({ silent: true })
    window.addEventListener('focus', refreshSilently)
    document.addEventListener('visibilitychange', refreshSilently)
    return () => {
      window.removeEventListener('focus', refreshSilently)
      document.removeEventListener('visibilitychange', refreshSilently)
    }
  }, [loadConversation])

  const send = async (text) => {
    const content = text.trim()
    if (!content) return
    try {
      setSending(true)
      const data = await replyConversation(Number(id), { content })
      setConversation(data)
      setMessages(data.messages || [])
      setInput('')
      setShowAI(false)
      if (inputRef.current) inputRef.current.textContent = ''
    } catch (error) {
      toast(error.message || '发送失败')
    } finally {
      setSending(false)
    }
  }

  const fillInput = (text) => {
    const content = String(text || '').trim()
    setInput(content)
    if (inputRef.current) inputRef.current.textContent = content
  }

  const loadAiReplies = async () => {
    try {
      setAiLoading(true)
      setAiError('')
      const data = await getReplySuggestions(Number(id))
      setAiReplies(data.suggestions || [])
    } catch (error) {
      setAiReplies([])
      setAiError(error.message || 'AI 建议加载失败')
    } finally {
      setAiLoading(false)
    }
  }

  const toggleAiReplies = async () => {
    const next = !showAI
    setShowAI(next)
    if (next && aiReplies.length === 0) {
      await loadAiReplies()
    }
  }

  const exchange = conversation?.contact_exchange
  const isAccepted = exchange?.status === 'accepted'
  const myName = role === 'recruiter' ? conversation?.recruiter_display_name : conversation?.seeker_display_name
  const peerName = role === 'recruiter' ? conversation?.seeker_display_name : conversation?.recruiter_display_name
  const peerId = role === 'recruiter' ? conversation?.seeker_id : conversation?.recruiter_id
  const homePath = role === 'recruiter' ? '/recruiter/jobs' : '/seeker/home'
  const homeLabel = role === 'recruiter' ? '我的岗位' : '首页'

  useEffect(() => {
    if (exchange?.status !== 'pending') return undefined
    const timer = window.setInterval(() => {
      loadConversation({ silent: true })
    }, 3000)
    return () => window.clearInterval(timer)
  }, [exchange?.status, loadConversation])

  const handleRequestExchange = async () => {
    try {
      const next = await requestContactExchange({ conversation_id: Number(id) })
      setConversation(prev => prev ? { ...prev, contact_exchange: next } : prev)
      toast('已发起联系方式交换请求')
    } catch (error) {
      toast(error.message || '请求失败')
    }
  }

  const handleAcceptExchange = async () => {
    try {
      const next = await reviewContactExchange(exchange.id, { action: 'accept' })
      setConversation(prev => prev ? { ...prev, contact_exchange: next } : prev)
      toast('已同意交换联系方式')
    } catch (error) {
      toast(error.message || '处理失败')
    }
  }

  const handleDeclineExchange = async () => {
    try {
      const next = await reviewContactExchange(exchange.id, { action: 'decline' })
      setConversation(prev => prev ? { ...prev, contact_exchange: next } : prev)
      toast('已暂不同意交换联系方式')
    } catch (error) {
      toast(error.message || '处理失败')
    }
  }

  return (
    <>
      <NavBar
        title={peerName || '对话'}
        right={(
          <>
            <HomeNavLink to={homePath} label={homeLabel} />
            {onRightAction ? <span onClick={() => onRightAction(navigate, conversation)}>查看资料 ›</span> : null}
          </>
        )}
      />
      <div className="page chat-page" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="grow" style={{ overflowY: 'auto', paddingBottom: 8 }}>
          {loading && <div className="ai-tip center" style={{ padding: '10px 0' }}>正在加载对话...</div>}
          {!loading && (
            <div className="ai-tip center" style={{ padding: '10px 0' }}>
              关于「{conversation?.job_title || `岗位 #${conversation?.job_id}`}」的沟通
            </div>
          )}
          {messages.map(message => {
            const mine = message.sender_role === role
            return (
              <div key={message.id} className={`msg ${mine ? 'me' : 'them'}`}>
                {!mine && <span className="avatar" style={{ background: pickColor(peerId || 0) }}>{(peerName || '对')[0]}</span>}
                <div>
                  <div className="bubble">
                    {message.content}
                    {message.moderation_status === 'masked' && <div className="interview-flag">已自动屏蔽联系方式</div>}
                  </div>
                </div>
              </div>
            )
          })}
          {isAccepted && <ContactCard contacts={exchange.contacts} role={role} />}
        </div>

        {showAI && (
          <div className="ai-suggests">
            <div className="as-hd">AI 建议回复</div>
            {aiLoading && <div className="ai-tip center" style={{ padding: '8px 0' }}>正在生成回复建议...</div>}
            {aiError && <div className="ai-tip center" style={{ padding: '8px 0', color: '#D14343' }}>{aiError}</div>}
            {aiReplies.map((reply, index) => (
              <div key={index} className="as-item" onClick={() => fillInput(reply.text || reply)}>
                {reply.style ? <span className="as-style">{reply.style}</span> : null}
                {reply.text || reply}
                <button
                  className="ai-btn"
                  style={{ marginLeft: 8, padding: '3px 8px' }}
                  onClick={(event) => {
                    event.stopPropagation()
                    send(reply.text || reply)
                  }}
                  disabled={sending}
                >
                  发送
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="chat-bar">
          <div className="row gap8" style={{ marginBottom: 8, flexWrap: 'wrap' }}>
            <button className="ai-btn" onClick={toggleAiReplies} disabled={aiLoading}>{aiLoading ? '生成中' : aiButtonLabel}</button>
            <ContactExchangeBar
              exchange={exchange}
              role={role}
              onRequest={handleRequestExchange}
              onAccept={handleAcceptExchange}
              onDecline={handleDeclineExchange}
            />
          </div>
          <div className="cb-input-row">
            <div
              ref={inputRef}
              className="cb-input"
              contentEditable
              suppressContentEditableWarning
              onInput={event => setInput(event.currentTarget.textContent || '')}
              style={{ minHeight: 20 }}
            />
            <button className="cb-send" onClick={() => send(input)} disabled={sending}>{sending ? '发送中' : '发送'}</button>
          </div>
          <div className="tiny muted" style={{ paddingTop: 8, textAlign: 'center' }}>
            {myName ? `当前身份：${myName}` : ''}
          </div>
        </div>
      </div>
    </>
  )
}

export function RealRecruiterChat() {
  return (
    <RealConversationPage
      role="recruiter"
      aiButtonLabel="AI 回复"
      onRightAction={(navigate) => navigate('/recruiter/talent')}
    />
  )
}

export function RealSeekerChat() {
  return (
    <RealConversationPage
      role="seeker"
      aiButtonLabel="AI 润色/回复"
    />
  )
}
