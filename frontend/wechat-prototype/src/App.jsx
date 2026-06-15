import React from 'react'
import { Routes, Route, Navigate, Outlet, useNavigate, useLocation, Link } from 'react-router-dom'
import { ToastProvider, Phone } from './components/ui.jsx'
import { RecruiterApp, RecruiterJobDetail, RecruiterRegister } from './recruiter/RecruiterPages.jsx'
import { RecruiterJobCreate, RecruiterJobReview, RecruiterChat, RecruiterJobUpload } from './recruiter/RecruiterFlow.jsx'
import { RecruiterCandidate, RecruiterStats } from './recruiter/RecruiterExtra.jsx'
import { RecruiterCompanyPortrait, RecruiterJobPortrait } from './recruiter/RecruiterPortrait.jsx'
import { RecruiterVisitors } from './recruiter/RecruiterVisitors.jsx'
import { RecruiterApplicationDetail, RecruiterTalentPool, RecruiterTalentDetail } from './recruiter/RecruiterTalentPool.jsx'
import RecruiterNotifications from './recruiter/RecruiterNotifications.jsx'
import RecruiterFunnel from './recruiter/RecruiterFunnel.jsx'
import { RecruiterInterviews, RecruiterInterviewDetail } from './recruiter/RecruiterInterview.jsx'
import { SeekerApp, SeekerRegister } from './seeker/SeekerPages.jsx'
import { SeekerJobDetail, SeekerProfileEdit, SeekerChat } from './seeker/SeekerFlow.jsx'
import { SeekerMatch, SeekerApply, SeekerApplications, SeekerFavorites, SeekerHistory, SeekerCompanyView, SeekerInterviewPrep } from './seeker/SeekerExtra.jsx'
import SeekerNotifications from './seeker/SeekerNotifications.jsx'
import { SeekerResumeUpload, SeekerPortrait } from './seeker/SeekerPortrait.jsx'
import { SeekerParseHistory } from './seeker/SeekerParseHistory.jsx'
import { SeekerParseDetail } from './seeker/SeekerParseDetail.jsx'
import { AdminReviewList, AdminReviewDetail } from './admin/AdminReview.jsx'
import {
  AdminCompanyCertificationList,
  AdminCompanyCertificationDesktopDetail,
} from './admin/AdminCompanyCertification.jsx'
import { Chatbot } from './common/Chatbot.jsx'
import { Login } from './common/Login.jsx'
import { Register } from './common/Register.jsx'
import { UserProfile } from './common/UserProfile.jsx'
import { ProfileProvider } from './common/ProfileContext.jsx'
import { AdminApp } from './admin/AdminApp.jsx'

/* 顶部演示控制条：在招聘者端 / 应聘者端之间切换 */
function DemoBar() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const isSeeker = pathname.startsWith('/seeker')
  const isRecruiter = pathname.startsWith('/recruiter')
  return (
    <div className="stage-header">
      <div className="stage-title">
        <span className="dot" />
        空岗信息发布对接平台
        <small>· 微信小程序高保真原型 · 双端核心链路</small>
      </div>
      <div className="role-switch">
        <button className={isRecruiter ? 'active' : ''} onClick={() => navigate('/recruiter/jobs')}>招聘者端</button>
        <button className={isSeeker ? 'active' : ''} onClick={() => navigate('/seeker/home')}>应聘者端</button>
      </div>
    </div>
  )
}

/* 把页面装进手机壳的舞台 */
function Stage({ children, label }) {
  return (
    <div className="stage">
      <DemoBar />
      <div className="phones-row">
        <Phone label={label}>{children}</Phone>
      </div>
    </div>
  )
}

/* 落地页 */
function Landing() {
  const navigate = useNavigate()
  return (
    <div className="stage">
      <div className="stage-header">
        <div className="stage-title"><span className="dot" />空岗信息发布对接平台 <small>· 高保真原型</small></div>
      </div>
      <div className="phones-row">
        <Phone label="落地页">
          <div className="navbar"><div className="nav-title">空岗对接平台</div></div>
          <div className="page" style={{ background: 'linear-gradient(170deg,#07C160 0%,#06AD56 40%,#10AEFF 120%)' }}>
            <div style={{ padding: '50px 24px 30px', color: '#fff' }}>
              <div style={{ fontSize: 13, opacity: .9, background: 'rgba(255,255,255,.15)', display: 'inline-block', padding: '4px 12px', borderRadius: 999 }}>⚡ AI 增强 · 隐私保护</div>
              <div style={{ fontSize: 30, fontWeight: 800, marginTop: 18, lineHeight: 1.3 }}>空岗信息<br />智能对接平台</div>
              <div style={{ fontSize: 14, opacity: .9, marginTop: 12, lineHeight: 1.7 }}>面向中小企业的 AI 招聘平台<br />AI 代写 · 智能推送 · 虚拟名保护</div>
            </div>
            <div style={{ background: '#fff', borderRadius: '20px 20px 0 0', minHeight: 360, marginTop: 10, padding: 24 }}>
              <div style={{ fontWeight: 600, marginBottom: 16, color: '#333' }}>请选择身份进入</div>
              <div className="opt-card" style={{ marginBottom: 14, padding: 18 }} onClick={() => navigate('/register?role=recruiter')}>
                <div className="row gap12">
                  <span style={{ fontSize: 28 }}>🏢</span>
                  <div className="grow"><div style={{ fontWeight: 600 }}>我是招聘者</div><div className="tiny muted">发布岗位 · AI 代写 · 智能筛选</div></div>
                  <span style={{ color: 'var(--wx-text-light)' }}>›</span>
                </div>
              </div>
              <div className="opt-card" style={{ padding: 18 }} onClick={() => navigate('/register?role=seeker')}>
                <div className="row gap12">
                  <span style={{ fontSize: 28 }}>💼</span>
                  <div className="grow"><div style={{ fontWeight: 600 }}>我是求职者</div><div className="tiny muted">关键词订阅 · AI 精准推荐</div></div>
                  <span style={{ color: 'var(--wx-text-light)' }}>›</span>
                </div>
              </div>
              <div className="center" style={{ marginTop: 18 }}>
                <span className="tiny" style={{ color: 'var(--wx-green)', cursor: 'pointer' }} onClick={() => navigate('/login')}>已有账号？立即登录 ›</span>
              </div>
              <div className="center" style={{ marginTop: 12 }}>
                <span className="tiny" style={{ color: 'var(--wx-text-2)' }} onClick={() => navigate('/admin')}>🖥 进入管理后台（桌面端）›</span>
              </div>
              <div className="ai-tip center" style={{ marginTop: 14 }}>演示提示：顶部可在两端间切换，AI 功能均为 mock 演示</div>
            </div>
          </div>
        </Phone>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route path="/" element={<Landing />} />

        {/* 招聘者端 */}
        <Route path="/recruiter/register" element={<Stage label="招聘者 · 注册认证"><RecruiterRegister /></Stage>} />
        <Route path="/recruiter/jobs" element={<Stage label="招聘者 · 我的岗位"><RecruiterApp /></Stage>} />
        <Route path="/recruiter/jobs/:jobId" element={<Stage label="招聘者 · 岗位详情"><RecruiterJobDetail /></Stage>} />
        <Route path="/recruiter/job/create" element={<Stage label="招聘者 · 发布岗位"><RecruiterJobCreate /></Stage>} />
        <Route path="/recruiter/job/upload" element={<Stage label="招聘者 · 批量导入"><RecruiterJobUpload /></Stage>} />
        <Route path="/recruiter/job/review" element={<Stage label="招聘者 · 发布审核"><RecruiterJobReview /></Stage>} />
        <Route path="/recruiter/chat/:id" element={<Stage label="招聘者 · 对话"><RecruiterChat /></Stage>} />
        <Route path="/recruiter/candidate" element={<Stage label="招聘者 · 候选人分析"><RecruiterCandidate /></Stage>} />
        <Route path="/recruiter/stats" element={<Stage label="招聘者 · 数据统计"><RecruiterStats /></Stage>} />
        <Route path="/recruiter/company-portrait" element={<Stage label="招聘者 · 企业画像"><RecruiterCompanyPortrait /></Stage>} />
        <Route path="/recruiter/job-portrait" element={<Stage label="招聘者 · 岗位画像"><RecruiterJobPortrait /></Stage>} />
        <Route path="/recruiter/job/visitors/:jobId" element={<Stage label="招聘者 · 访客穿透"><RecruiterVisitors /></Stage>} />
        <Route path="/recruiter/talent" element={<Stage label="招聘者 · 人才池"><RecruiterTalentPool /></Stage>} />
        <Route path="/recruiter/applications/:applicationId" element={<Stage label="招聘者 · 投递详情"><RecruiterApplicationDetail /></Stage>} />
        <Route path="/recruiter/talent/:id" element={<Stage label="招聘者 · 人才详情"><RecruiterTalentDetail /></Stage>} />
        <Route path="/recruiter/notifications" element={<Stage label="招聘者 · 通知中心"><RecruiterNotifications /></Stage>} />
        <Route path="/recruiter/funnel" element={<Stage label="招聘者 · 招聘漏斗"><RecruiterFunnel /></Stage>} />
        <Route path="/recruiter/interviews" element={<Stage label="招聘者 · 面试管理"><RecruiterInterviews /></Stage>} />
        <Route path="/recruiter/interview/:id" element={<Stage label="招聘者 · 面试详情"><RecruiterInterviewDetail /></Stage>} />

        {/* 应聘者端 */}
        <Route element={<ProfileProvider><Outlet /></ProfileProvider>}>
          <Route path="/seeker/register" element={<Stage label="应聘者 · 注册"><SeekerRegister /></Stage>} />
          <Route path="/seeker/home" element={<Stage label="应聘者 · 发现岗位"><SeekerApp /></Stage>} />
          <Route path="/seeker/job/:id" element={<Stage label="应聘者 · 职位详情"><SeekerJobDetail /></Stage>} />
          <Route path="/seeker/match/:id" element={<Stage label="应聘者 · 人岗匹配"><SeekerMatch /></Stage>} />
          <Route path="/seeker/apply/:id" element={<Stage label="应聘者 · 投递简历"><SeekerApply /></Stage>} />
          <Route path="/seeker/applications" element={<Stage label="应聘者 · 投递记录"><SeekerApplications /></Stage>} />
          <Route path="/seeker/favorites" element={<Stage label="应聘者 · 我的收藏"><SeekerFavorites /></Stage>} />
          <Route path="/seeker/history" element={<Stage label="应聘者 · 浏览记录"><SeekerHistory /></Stage>} />
          <Route path="/seeker/interview-prep" element={<Stage label="应聘者 · 面试准备"><SeekerInterviewPrep /></Stage>} />
          <Route path="/seeker/resume" element={<Stage label="应聘者 · 上传简历"><SeekerResumeUpload /></Stage>} />
          <Route path="/seeker/portrait" element={<Stage label="应聘者 · 简历画像"><SeekerPortrait /></Stage>} />
          <Route path="/seeker/parse-history" element={<Stage label="应聘者 · 解析历史"><SeekerParseHistory /></Stage>} />
          <Route path="/seeker/parse-history/:uploadId" element={<Stage label="应聘者 · 解析详情"><SeekerParseDetail /></Stage>} />
          <Route path="/seeker/company-portrait" element={<Stage label="应聘者 · 企业画像"><SeekerCompanyView /></Stage>} />
          <Route path="/seeker/profile/edit" element={<Stage label="应聘者 · 完善信息"><SeekerProfileEdit /></Stage>} />
          <Route path="/seeker/notifications" element={<Stage label="应聘者 · 通知中心"><SeekerNotifications /></Stage>} />
          <Route path="/seeker/chat/:id" element={<Stage label="应聘者 · 对话"><SeekerChat /></Stage>} />
        </Route>

        {/* 通用 */}
        <Route path="/login" element={<Stage label="登录"><Login /></Stage>} />
        <Route path="/register" element={<Stage label="注册"><Register /></Stage>} />
        <Route path="/profile" element={<Stage label="个人信息"><UserProfile /></Stage>} />
        <Route path="/support" element={<Stage label="AI 智能客服"><Chatbot /></Stage>} />

        {/* 管理后台（桌面全屏，不装手机壳） */}
        <Route path="/admin" element={<AdminApp />} />
        <Route path="/admin/review/:id" element={<AdminReviewDetail />} />

        {/* 管理后台 - 企业认证审核（真实API） */}
        <Route path="/admin/company-certifications" element={<Stage label="管理员 · 企业认证审核"><AdminCompanyCertificationList /></Stage>} />
        <Route path="/admin/company-certification/:id" element={<AdminCompanyCertificationDesktopDetail />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ToastProvider>
  )
}
