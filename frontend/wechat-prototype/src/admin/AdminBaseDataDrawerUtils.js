export function buildStandardPositionPayload(form) {
  return {
    name: form.name.trim(),
    category: form.category.trim(),
    aliases: form.aliasesText.split(',').map(item => item.trim()).filter(Boolean),
    description: form.description.trim() || null,
    status: form.status,
  }
}

export function buildTagPayload(form) {
  return {
    name: form.name.trim(),
    category: form.category.trim(),
    parent_id: form.parentId ? Number(form.parentId) : null,
    color: form.color.trim() || null,
    description: form.description.trim() || null,
    sort_order: Number(form.sortOrder) || 0,
    status: form.status,
  }
}

export function validateStandardPositionForm(form) {
  const errors = {}
  if (!form.name.trim()) errors.name = '请填写标准名称'
  if (!form.category.trim()) errors.category = '请填写分类'
  return errors
}

export function validateTagForm(form) {
  const errors = {}
  if (!form.name.trim()) errors.name = '请填写标签名称'
  if (!form.category.trim()) errors.category = '请填写分类'
  const sortOrder = Number(form.sortOrder)
  if (!Number.isInteger(sortOrder) || sortOrder < 0) errors.sortOrder = '排序必须是非负整数'
  return errors
}

export function filterTagParentOptions(tags, editingId) {
  return tags.filter(tag => Number(tag.id) !== Number(editingId))
}
