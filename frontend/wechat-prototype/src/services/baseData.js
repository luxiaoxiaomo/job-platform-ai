import { get, post, put } from './api.js'

export async function listStandardPositions(params = {}) {
  return get('/api/v1/base-data/standard-positions', params)
}

export async function getStandardPosition(id) {
  return get(`/api/v1/base-data/standard-positions/${id}`)
}

export async function listPublicStandardPositions(params = {}) {
  return get('/api/v1/base-data/standard-positions/public', params)
}

export async function createStandardPosition(data) {
  return post('/api/v1/base-data/standard-positions', data)
}

export async function updateStandardPosition(id, data) {
  return put(`/api/v1/base-data/standard-positions/${id}`, data)
}

export async function listTagLibraryItems(params = {}) {
  return get('/api/v1/base-data/tags', params)
}

export async function getTagLibraryItem(id) {
  return get(`/api/v1/base-data/tags/${id}`)
}

export async function listPublicTagLibraryItems(params = {}) {
  return get('/api/v1/base-data/tags/public', params)
}

export async function createTagLibraryItem(data) {
  return post('/api/v1/base-data/tags', data)
}

export async function updateTagLibraryItem(id, data) {
  return put(`/api/v1/base-data/tags/${id}`, data)
}

export async function listBaseDataOperationLogs(params = {}) {
  return get('/api/v1/base-data/operation-logs', params)
}
