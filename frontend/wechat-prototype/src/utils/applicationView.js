export const applicationStatusText = {
  submitted: '已投递',
  viewed: '已查看',
  interview_invited: '邀面',
  rejected: '已拒绝',
  hired: '已录用',
}

export const applicationStatusTag = {
  submitted: 'tag-gray',
  viewed: 'tag-blue',
  interview_invited: 'tag-green',
  rejected: 'tag-gray',
  hired: 'tag-green',
}

export function formatDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
