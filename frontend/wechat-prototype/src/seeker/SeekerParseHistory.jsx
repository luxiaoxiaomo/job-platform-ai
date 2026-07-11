import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar, HomeNavLink } from '../components/ui.jsx'
import { getUploadStatusDisplay, getParseStatusDisplay } from '../utils/resumeStatus.js'
import { listMyUploads } from '../services/index.js'

export function SeekerParseHistory() {
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    listMyUploads(20)
      .then(data => {
        setHistory(Array.isArray(data) ? data : [])
        setError('')
      })
      .catch(err => {
        setHistory([])
        setError(err.message || '上传历史加载失败')
      })
      .finally(() => setLoading(false))
  }, [])

  const formatFileSize = (bytes) => {
    if (!bytes && bytes !== 0) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDateTime = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hour = String(date.getHours()).padStart(2, '0')
    const minute = String(date.getMinutes()).padStart(2, '0')
    return `${month}-${day} ${hour}:${minute}`
  }

  const getStatusColor = (status) => {
    const colors = { green: '#07C160', orange: '#FA9D3B', red: '#FA5151', gray: '#999', blue: '#576B95' }
    return colors[status.color] || colors.gray
  }

  return (
    <>
      <NavBar title="解析历史" right={<HomeNavLink />} />
      <div className="page" style={{ paddingBottom: 60 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>加载中…</div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#FA5151' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>⚠️</div>
            <div>{error}</div>
          </div>
        ) : history.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📄</div>
            <div>还没有上传记录</div>
            <button className="btn btn-primary" style={{ marginTop: 20, width: 'auto', padding: '0 24px' }}
              onClick={() => navigate('/seeker/resume')}>去上传简历</button>
          </div>
        ) : (
          <>
            <div className="cell-group-title">共 {history.length} 次上传记录</div>
            {history.map((item) => {
              const upload = item.upload || {}
              const run = item.latest_parse_run
              const uploadStatus = getUploadStatusDisplay(upload.status)
              const parseStatus = run ? getParseStatusDisplay(run.status) : null
              const hasError = upload.error_message || (run && run.error_message)

              return (
                <div key={upload.id} className="cell-group" style={{ marginBottom: 12 }}>
                  <div className="cell" onClick={() => run && navigate(`/seeker/parse-history/${run.id}`)}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 500, marginBottom: 4 }}>{upload.original_file_name || '简历文件'}</div>
                      <div style={{ fontSize: 12, color: '#999', marginBottom: 8 }}>
                        {formatDateTime(upload.created_at)} · {formatFileSize(upload.file_size)}
                      </div>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span style={{ fontSize: 12, color: getStatusColor(uploadStatus), fontWeight: 500 }}>
                          {uploadStatus.label}
                        </span>
                        {parseStatus && (
                          <>
                            <span style={{ fontSize: 12, color: '#ddd' }}>|</span>
                            <span style={{ fontSize: 12, color: getStatusColor(parseStatus), fontWeight: 500 }}>
                              {parseStatus.label}
                            </span>
                          </>
                        )}
                      </div>
                      {hasError && (
                        <div style={{ marginTop: 8, padding: '6px 10px', background: '#FFF1F0', borderRadius: 4, fontSize: 12, color: '#FA5151' }}>
                          ⚠️ {upload.error_message || run.error_message}
                        </div>
                      )}
                    </div>
                    {run && <span className="cell-arrow">›</span>}
                  </div>
                </div>
              )
            })}
          </>
        )}

        <div className="btn-block-wrap">
          <button className="btn btn-primary" onClick={() => navigate('/seeker/resume')}>上传新简历</button>
        </div>
      </div>
    </>
  )
}
