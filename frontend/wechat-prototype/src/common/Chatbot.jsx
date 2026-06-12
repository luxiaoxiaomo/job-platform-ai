import React, { useState, useRef, useEffect } from 'react'
import { NavBar, AIBadge, useToast } from '../components/ui.jsx'
import { chatbotFAQ, chatbotAnswers } from '../mock/data.js'

/* ============ AI 智能客服（双端通用 /support） ============ */
export function Chatbot() {
  const toast = useToast()
  const [msgs, setMsgs] = useState([
    { from: 'bot', text: '你好！我是平台智能助手，有什么可以帮你？你可以点下方常见问题，或直接输入。', faq: true },
  ])
  const [input, setInput] = useState('')
  const [transferred, setTransferred] = useState(false)
  const [unknownCount, setUnknownCount] = useState(0)
  const endRef = useRef(null)
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs])

  const ask = (q) => {
    const text = (q || '').trim()
    if (!text) return
    setMsgs(m => [...m, { from: 'me', text }])
    setInput('')
    setTimeout(() => {
      const ans = chatbotAnswers[text]
      if (ans) {
        setMsgs(m => [...m, { from: 'bot', text: ans, ai: true }])
        setUnknownCount(0)
      } else {
        const next = unknownCount + 1
        setUnknownCount(next)
        if (next >= 2) {
          setMsgs(m => [...m, { from: 'bot', text: '抱歉这个问题我暂时无法准确解答，已为你转接人工客服（工作时间 9:00-18:00），稍后会有专员联系你。', transfer: true }])
          setTransferred(true)
        } else {
          setMsgs(m => [...m, { from: 'bot', text: '我理解你的问题，但还需要确认一下。你可以换个说法，或从下方常见问题中选择～', faq: true, ai: true }])
        }
      }
    }, 600)
  }

  return (
    <>
      <NavBar title="智能客服" right={!transferred && <span onClick={() => { setTransferred(true); toast('已转接人工'); setMsgs(m => [...m, { from: 'bot', text: '已为你转接人工客服，请稍候。', transfer: true }]) }}>转人工</span>} />
      <div className="page chat-page" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="grow" style={{ overflowY: 'auto', padding: '8px 0' }}>
          {msgs.map((m, i) => (
            <div key={i}>
              <div className={`msg ${m.from === 'me' ? 'me' : 'them'}`}>
                {m.from === 'bot' && <span className="avatar" style={{ background: 'var(--ai-grad)' }}>⚡</span>}
                <div>
                  <div className="bubble">
                    {m.ai && <div style={{ marginBottom: 4 }}><AIBadge>AI</AIBadge></div>}
                    {m.text}
                    {m.transfer && <div className="interview-flag" style={{ background: '#EFF8FF', color: 'var(--wx-blue)' }}>🧑‍💼 已转人工</div>}
                  </div>
                  {/* FAQ 快捷问 */}
                  {m.faq && (
                    <div style={{ marginTop: 8 }}>
                      {chatbotFAQ.map(q => (
                        <div key={q} onClick={() => ask(q)}
                          style={{ display: 'inline-block', background: '#fff', border: '0.5px solid var(--ai-border)', color: 'var(--wx-green-dark)', borderRadius: 999, padding: '5px 12px', fontSize: 12, margin: '0 6px 6px 0' }}>
                          {q}
                        </div>
                      ))}
                    </div>
                  )}
                  {m.from === 'bot' && m.ai && !m.faq && (
                    <div className="tiny" style={{ color: 'var(--wx-text-light)', marginTop: 4 }}>此回答由 AI 生成 ·
                      <span style={{ color: 'var(--wx-green-dark)' }} onClick={() => toast('感谢反馈')}> 有用</span> /
                      <span style={{ color: 'var(--wx-text-2)' }} onClick={() => { setTransferred(true); setMsgs(mm => [...mm, { from: 'bot', text: '抱歉没帮上忙，已为你转接人工客服。', transfer: true }]) }}> 没用</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>

        <div className="chat-bar">
          <div className="cb-input-row">
            <input className="cb-input" value={input} placeholder="输入你的问题…" onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && ask(input)} />
            <button className="cb-send" onClick={() => ask(input)}>发送</button>
          </div>
        </div>
      </div>
    </>
  )
}
