import { get, post } from './api.js'

export async function listMyConversations(params = {}) {
  return get('/api/v1/messages/conversations', params)
}

export async function getConversation(conversationId) {
  return get(`/api/v1/messages/conversations/${conversationId}`)
}

export async function sendJobMessage(data) {
  return post('/api/v1/messages/messages', data)
}

export async function openJobConversation(data) {
  return post('/api/v1/messages/conversations/open', data)
}

export async function replyConversation(conversationId, data) {
  return post(`/api/v1/messages/conversations/${conversationId}/messages`, data)
}

export async function getReplySuggestions(conversationId) {
  return post(`/api/v1/messages/conversations/${conversationId}/reply-suggestions`, {})
}

export async function requestContactExchange(data) {
  return post('/api/v1/messages/contact-exchanges', data)
}

export async function reviewContactExchange(exchangeId, data) {
  return post(`/api/v1/messages/contact-exchanges/${exchangeId}/review`, data)
}

export async function getContactExchangeStats() {
  return get('/api/v1/messages/contact-exchanges/stats/summary')
}
