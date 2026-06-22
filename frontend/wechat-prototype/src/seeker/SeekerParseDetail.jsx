import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { NavBar, HomeNavLink } from '../components/ui.jsx'
import { getUploadStatusDisplay, getParseStatusDisplay } from '../utils/resumeStatus.js'
import { getParseRunDetail } from '../services/index.js'

export function SeekerParseDetail() {
  const navigate = useNavigate()
  const { uploadId } = useParams() // 路由参数名沿用 uploadId，实际传的是 parse_run_id
  const parseRunId = uploadId
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    getParseRunDetail(parseRunId)
      .then(data => { setDetail(data); setError('') })
      .catch(err => { setDetail(null); setError(err.message || '解析详情加载失败') })
      .finally(() => setLoading(false))
  }, [parseRunId])

  const formatDateTime = (dateStr) => {
    if (!dateStr) return ''
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    })
  }

  const formatFileSize = (bytes) => {
    if (!bytes && bytes !== 0) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getStatusColor = (status) => {
    const colors = { green: '#07C160', orange: '#FA9D3B', red: '#FA5151', gray: '#999', blue: '#576B95' }
    return colors[status.color] || colors.gray
  }

  if (loading) {
    return (
      <>
        <NavBar title="解析详情" right={<HomeNavLink />} />
        <div className="page" style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>加载中…</div>
      </>
    )
  }

  if (error || !detail) {
    return (
      <>
        <NavBar title="解析详情" right={<HomeNavLink />} />
        <div className="page" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
          <div style={{ color: '#999' }}>{error || '记录不存在'}</div>
          <button className="btn btn-default" style={{ marginTop: 20, width: 'auto', padding: '0 24px' }}
            onClick={() => navigate('/seeker/parse-history')}>返回历史列表</button>
        </div>
      </>
    )
  }

  const upload = detail.upload || {}
  const run = detail.parse_run || {}
  const extracted = detail.extracted_text
  const chunks = detail.chunks || []
  const uploadStatus = getUploadStatusDisplay(upload.status)
  const parseStatus = getParseStatusDisplay(run.status)

  return (
    <>
      <NavBar title="解析详情" right={<HomeNavLink />} />
      <div className="page" style={{ paddingBottom: 80 }}>

        <div className="cell-group-title">基础信息</div>
        <div className="cell-group">
          <div className="cell"><span className="cell-label">文件名</span><span className="cell-value">{upload.original_file_name}</span></div>
          <div className="cell"><span className="cell-label">文件大小</span><span className="cell-value">{formatFileSize(upload.file_size)}</span></div>
          <div className="cell"><span className="cell-label">上传时间</span><span className="cell-value">{formatDateTime(upload.created_at)}</span></div>
          <div className="cell"><span className="cell-label">上传状态</span><span className="cell-value" style={{ color: getStatusColor(uploadStatus), fontWeight: 500 }}>{uploadStatus.label}</span></div>
          <div className="cell"><span className="cell-label">解析状态</span><span className="cell-value" style={{ color: getStatusColor(parseStatus), fontWeight: 500 }}>{parseStatus.label}</span></div>
        </div>

        {(upload.error_message || run.error_message) && (
          <>
            <div className="cell-group-title">错误信息</div>
            <div className="cell-group">
              <div style={{ padding: 16 }}>
                <div style={{ padding: '12px 16px', background: '#FFF1F0', borderRadius: 8, fontSize: 14, color: '#FA5151', lineHeight: 1.6 }}>
                  ⚠️ {upload.error_message || run.error_message}
                </div>
              </div>
            </div>
          </>
        )}

        {extracted && (
          <>
            <div className="cell-group-title">
              原文预览
              {(extracted.quality_score !== null && extracted.quality_score !== undefined) && (
                <span style={{ marginLeft: 8, fontSize: 12, color: '#999' }}>质量分: {Math.round(extracted.quality_score * 100)}/100</span>
              )}
            </div>
            <div className="cell-group">
              <div style={{ padding: 16 }}>
                <div style={{ padding: '16px', background: '#F7F8FA', borderRadius: 8, fontSize: 13, lineHeight: 1.8, color: '#333', whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'auto' }}>
                  {extracted.text_preview}
                </div>
                <div style={{ marginTop: 12, fontSize: 12, color: '#999', textAlign: 'center' }}>
                  共 {extracted.char_count} 字 · {chunks.length} 个文本块
                </div>
              </div>
            </div>
          </>
        )}

        <div className="btn-block-wrap">
          <button className="btn btn-default" onClick={() => navigate('/seeker/parse-history')}>返回历史列表</button>
          {run.status === 'succeeded' && (
            <>
              <button className="btn btn-default" onClick={() => navigate('/seeker/portrait')}>查看画像</button>
              <button className="btn btn-primary" onClick={() => navigate(`/seeker/parse-confirm/${parseRunId}`)}>确认解析结果</button>
            </>
          )}
        </div>
      </div>
    </>
  )
}
