/**
 * 简历解析状态映射工具
 * 对应 P1 阶段后端状态枚举
 */

// upload.status 状态映射
export const UPLOAD_STATUS = {
  uploaded: { label: '已上传', color: 'blue' },
  processing: { label: '解析中', color: 'orange' },
  parsed: { label: '已解析', color: 'green' },
  failed: { label: '解析失败', color: 'red' }
}

// parse_run.status 状态映射
export const PARSE_STATUS = {
  pending: { label: '等待解析', color: 'gray' },
  running: { label: '解析中', color: 'orange' },
  succeeded: { label: '解析完成', color: 'green' },
  completed_with_errors: { label: '部分完成', color: 'orange' },
  failed: { label: '解析失败', color: 'red' }
}

/**
 * 获取上传状态显示信息
 * @param {string} status - 后端返回的 upload.status
 * @returns {{label: string, color: string}}
 */
export function getUploadStatusDisplay(status) {
  return UPLOAD_STATUS[status] || { label: '未知状态', color: 'gray' }
}

/**
 * 获取解析状态显示信息
 * @param {string} status - 后端返回的 parse_run.status
 * @returns {{label: string, color: string}}
 */
export function getParseStatusDisplay(status) {
  return PARSE_STATUS[status] || { label: '未知状态', color: 'gray' }
}

/**
 * P0 阶段：兼容当前简单状态
 * 根据 resume.parsed_snapshot 判断状态
 */
export function getLegacyResumeStatus(resume) {
  if (!resume) {
    return { label: '未上传', color: 'gray' }
  }
  if (resume.parsed_snapshot && resume.parsed_snapshot.trim()) {
    return { label: '已解析', color: 'green' }
  }
  return { label: '待解析', color: 'orange' }
}
