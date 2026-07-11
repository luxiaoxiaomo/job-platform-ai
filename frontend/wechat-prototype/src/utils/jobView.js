import { getPublicJob } from '../services/index.js'

export function formatSalary(job) {
  if (!job) return ''
  if (job.salary_min && job.salary_max) return `${job.salary_min}K-${job.salary_max}K`
  if (job.salary_min) return `${job.salary_min}K+`
  return ''
}

export function mapPublicJobToView(job) {
  if (!job) return null
  const company = job.recruiter_display_name || '认证企业'
  return {
    id: job.id,
    name: job.title,
    salary: formatSalary(job),
    city: job.city,
    exp: job.experience,
    edu: job.education,
    tags: job.tags || [],
    tagRefs: job.tag_refs || [],
    companyShow: company,
    matchScore: 80,
    aiHighlight: '岗位已通过平台审核，当前对求职者可见。',
    duty: job.description || '暂无岗位职责说明。',
    require: job.requirement || '暂无任职要求说明。',
    contactMethod: '平台内沟通',
    virtual: false,
    raw: job,
    recruiterId: job.recruiter_id,
  }
}

export async function findPublicJobById(jobId) {
  const job = await getPublicJob(jobId)
  return mapPublicJobToView(job)
}
