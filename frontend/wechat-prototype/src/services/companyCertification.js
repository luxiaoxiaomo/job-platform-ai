import { get, post, postForm } from './api.js'

export async function getMyCompanyCertification() {
  return get('/api/v1/company-certifications/me')
}

export async function submitCompanyCertification(data) {
  return post('/api/v1/company-certifications/me', data)
}

export async function uploadBusinessLicenseForOcr(file) {
  const formData = new FormData()
  formData.append('file', file)
  return postForm('/api/v1/company-certifications/license/ocr', formData)
}

export async function uploadCertificationProofFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return postForm('/api/v1/company-certifications/proof-file', formData)
}

export async function getPublicCompanyCertification(recruiterId) {
  return get(`/api/v1/company-certifications/public/recruiters/${recruiterId}`)
}

export async function listCompanyCertifications(params = {}) {
  return get('/api/v1/company-certifications/admin', params)
}

export async function getCompanyCertification(certificationId) {
  return get(`/api/v1/company-certifications/admin/${certificationId}`)
}

export async function reviewCompanyCertification(certificationId, data) {
  return post(`/api/v1/company-certifications/admin/${certificationId}/review`, data)
}
