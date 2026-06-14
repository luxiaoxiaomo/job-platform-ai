import React, { createContext, useContext, useEffect, useState } from 'react'
import { getMyResume } from '../services/index.js'

const ProfileCtx = createContext(null)

export function ProfileProvider({ children }) {
  const [completed, setCompleted] = useState(false)
  const [hasResume, setHasResume] = useState(false)
  const [resume, setResume] = useState(null)
  const unlocked = completed && hasResume

  const refreshResume = async () => {
    const token = localStorage.getItem('access_token')
    const userInfo = localStorage.getItem('user_info')
    if (!token || !userInfo) return null
    const user = JSON.parse(userInfo)
    if (user.role !== 'seeker') return null

    const data = await getMyResume()
    setHasResume(!!data.has_resume)
    setResume(data.resume || null)
    return data.resume || null
  }

  useEffect(() => {
    refreshResume().catch(() => {
      setHasResume(false)
      setResume(null)
    })
  }, [])

  const markCompleted = () => setCompleted(true)
  const markResume = (nextResume = null) => {
    setHasResume(true)
    if (nextResume) setResume(nextResume)
  }

  return (
    <ProfileCtx.Provider value={{ completed, hasResume, resume, unlocked, markCompleted, markResume, refreshResume }}>
      {children}
    </ProfileCtx.Provider>
  )
}

export function useProfile() {
  const ctx = useContext(ProfileCtx)
  if (!ctx) throw new Error('useProfile must be inside ProfileProvider')
  return ctx
}
