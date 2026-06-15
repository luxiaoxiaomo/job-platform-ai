import React from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar } from '../components/ui.jsx'
import { getUploadStatusDisplay, getParseStatusDisplay } from '../utils/resumeStatus.js'
import { mockParseHistoryP1, mockExtractedTextP1 } from '../mock/resumeP1.js'

export function SeekerParseDetail() {
  const navigate = useNavigate()
  const { uploadId } = useParams()

  // Mock 数据：根据 uploadId 查找记录
  const record = mockParseHistoryP1.find(item => item.upload_id === parseInt(uploadId))
  const extractedText = mockExtractedTextP1 // P1 阶段用固定 mock 数据

  if (!record) {
    return (
      <>
        <NavBar title="解析详情" />
        <div className="page" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
          <div style={{ color: '#999' }}>记录不存在</div>
          <button
            className="btn btn-default"
            style={{ marginTop: 20 }}
            onClick={() => navigate('/seeker/parse-history')}
          >
            返回历史列表
          </button>
        </div>
      </>
    )
  }

  const uploadStatus = getUploadStatusDisplay(record.upload_status)
  const parseStatus = getParseStatusDisplay(record.parse_status)

  const formatDateTime = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
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
      <NavBar title="解析详情" />
      <div className="page" style={{ paddingBottom: 80 }}>

        {/* 基础信息 */}
        <div className="cell-group-title">基础信息</div>
        <div className="cell-group">
          <div className="cell">
            <span className="cell-label">文件名</span>
            <span className="cell-value">{record.file_name}</span>
          </div>
          <div className="cell">
            <span className="cell-label">文件大小</span>
            <span className="cell-value">{formatFileSize(record.file_size)}</span>
          </div>
          <div className="cell">
            <span className="cell-label">上传时间</span>
            <span className="cell-value">{formatDateTime(record.upload_time)}</span>
          </div>
          <div className="cell">
            <span className="cell-label">上传状态</span>
            <span className="cell-value" style={{
              color: getStatusColor(uploadStatus),
              fontWeight: 500
            }}>
              {uploadStatus.label}
            </span>
          </div>
          <div className="cell">
            <span className="cell-label">解析状态</span>
            <span className="cell-value" style={{
              color: getStatusColor(parseStatus),
              fontWeight: 500
            }}>
              {parseStatus.label}
            </span>
          </div>
        </div>

        {/* 错误信息 */}
        {record.error_message && (
          <>
            <div className="cell-group-title">错误信息</div>
            <div className="cell-group">
              <div style={{ padding: 16 }}>
                <div style={{
                  padding: '12px 16px',
                  background: '#FFF1F0',
                  borderRadius: 8,
                  fontSize: 14,
                  color: '#FA5151',
                  lineHeight: 1.6
                }}>
                  ⚠️ {record.error_message}
                </div>
              </div>
            </div>
          </>
        )}

        {/* 原文预览 */}
        {extractedText && !record.error_message && (
          <>
            <div className="cell-group-title">
              原文预览
              {extractedText.quality_score && (
                <span style={{ marginLeft: 8, fontSize: 12, color: '#999' }}>
                  质量分: {extractedText.quality_score}/100
                </span>
              )}
            </div>
            <div className="cell-group">
              <div style={{ padding: 16 }}>
                <div style={{
                  padding: '16px',
                  background: '#F7F8FA',
                  borderRadius: 8,
                  fontSize: 13,
                  lineHeight: 1.8,
                  color: '#333',
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                  maxHeight: 500,
                  overflow: 'auto'
                }}>
                  {extractedText.full_text}
                </div>

                {extractedText.page_count && (
                  <div style={{
                    marginTop: 12,
                    fontSize: 12,
                    color: '#999',
                    textAlign: 'center'
                  }}>
                    共 {extractedText.page_count} 页 · {extractedText.word_count} 字
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* 操作按钮 */}
        <div className="btn-block-wrap">
          <button
            className="btn btn-default"
            onClick={() => navigate('/seeker/parse-history')}
          >
            返回历史列表
          </button>
          {record.parse_status === 'succeeded' && (
            <button
              className="btn btn-primary"
              onClick={() => navigate('/seeker/portrait')}
            >
              查看简历画像
            </button>
          )}
        </div>
      </div>
    </>
  )
}
