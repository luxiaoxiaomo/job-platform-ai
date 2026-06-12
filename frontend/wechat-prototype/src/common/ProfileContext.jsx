import React, { createContext, useContext, useState } from 'react'

/* ============================================================
   应聘者补充信息状态（mock 后端状态）
   - completed: 必填字段是否已填（基本信息 + 联系方式）
   - hasResume: 是否已上传简历
   - unlocked: 是否满足"查看完整信息 + 投递"的前置条件
   ============================================================ */
const ProfileCtx = createContext(null)

export function ProfileProvider({ children }) {
  const [completed, setCompleted] = useState(false)   // 必填项已填
  const [hasResume, setHasResume] = useState(false)   // 已上传简历
  // unlocked = completed && hasResume（两个条件都满足才能解锁）
  const unlocked = completed && hasResume

  const markCompleted = () => setCompleted(true)
  const markResume = () => setHasResume(true)

  return (
    <ProfileCtx.Provider value={{ completed, hasResume, unlocked, markCompleted, markResume }}>
      {children}
    </ProfileCtx.Provider>
  )
}

export function useProfile() {
  const ctx = useContext(ProfileCtx)
  if (!ctx) throw new Error('useProfile must be inside ProfileProvider')
  return ctx
}
