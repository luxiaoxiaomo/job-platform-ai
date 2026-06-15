import React from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar } from '../components/ui.jsx'
import { getUploadStatusDisplay, getParseStatusDisplay } from '../utils/resumeStatus.js'
import { mockParseHistoryP1 } from '../mock/resumeP1.js'

export function SeekerParseHistory() {
  const navigate = useNavigate()
  const history = mockParseHistoryP1

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDateTime = (dateStr) => {
    const date = new Date(dateStr)
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hour = String(date.getHours()).padStart(2, '0')
    const minute = String(date.getMinutes()).padStart(2, '0')
    return `${month}-${day} ${hour}:${minute}`
  }

  const getStatusColor = (status) => {
    const colors = {
      green: '#07C160',
      orange: '#FA9D3B',
      red: '#FA5151',
      gray: '#999',
      blue: '#576B95'
    }
    return colors[status.color] || colors.gray
  }

  return (
    <>
      <NavBar title="解析历史" />
      <div className="page" style={{ paddingBottom: 60 }}>
        <div className="cell-group-title">
          共 {history.length} 次上传记录
        </div>

        {history.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📄</div>
            <div>还没有上传记录</div>
          </div>
        ) : (
          history.map((item) => {
            const uploadStatus = getUploadStatusDisplay(item.upload_status)
            const parseStatus = getParseStatusDisplay(item.parse_status)
            const hasError = item.error_message

            return (
              <div key={item.upload_id} className="cell-group" style={{ marginBottom: 12 }}>
                <div className="cell" onClick={() => navigate(`/seeker/parse-history/${item.upload_id}`)}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                      <span style={{ fontWeight: 500 }}>{item.file_name}</span>
                    </div>

                    <div style={{ fontSize: 12, color: '#999', marginBottom: 8 }}>
                      {formatDateTime(item.upload_time)} · {formatFileSize(item.file_size)}
                    </div>

                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span style={{
                        fontSize: 12,
                        color: getStatusColor(uploadStatus),
                        fontWeight: 500
                      }}>
                        {uploadStatus.label}
                      </span>
                      <span style={{ fontSize: 12, color: '#ddd' }}>|</span>
                      <span style={{
                        fontSize: 12,
                        color: getStatusColor(parseStatus),
                        fontWeight: 500
                      }}>
                        {parseStatus.label}
                      </span>
                    </div>

                    {hasError && (
                      <div style={{
                        marginTop: 8,
                        padding: '6px 10px',
                        background: '#FFF1F0',
                        borderRadius: 4,
                        fontSize: 12,
                        color: '#FA5151'
                      }}>
                        ⚠️ {item.error_message}
                      </div>
                    )}

                    {item.extracted_text_preview && !hasError && (
                      <div style={{
                        marginTop: 8,
                        padding: '8px 10px',
                        background: '#F7F8FA',
                        borderRadius: 4,
                        fontSize: 12,
                        color: '#666',
                        lineHeight: 1.5,
                        maxHeight: 60,
                        overflow: 'hidden',
                        whiteSpace: 'pre-wrap'
                      }}>
                        {item.extracted_text_preview.substring(0, 80)}
                        {item.extracted_text_preview.length > 80 && '...'}
                      </div>
                    )}
                  </div>
                  <span className="cell-arrow">›</span>
                </div>
              </div>
            )
          })
        )}

        <div className="btn-block-wrap">
          <button className="btn btn-primary" onClick={() => navigate('/seeker/resume')}>
            上传新简历
          </button>
        </div>
      </div>
    </>
  )
}
