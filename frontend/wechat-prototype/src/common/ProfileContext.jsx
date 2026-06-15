import React, { createContext, useContext, useEffect, useState } from 'react'
import { getMyResume, getMySeekerProfile, saveMySeekerProfile } from '../services/index.js'

const ProfileCtx = createContext(null)

export function ProfileProvider({ children }) {
  const [completed, setCompleted] = useState(false)
  const [hasResume, setHasResume] = useState(false)
  const [resume, setResume] = useState(null)
  const [profile, setProfile] = useState(null)
  const unlocked = completed && hasResume

  const canLoadSeekerData = () => {
    const token = localStorage.getItem('access_token')
    const userInfo = localStorage.getItem('user_info')
    if (!token || !userInfo) return false
    const user = JSON.parse(userInfo)
    return user.role === 'seeker'
  }

  const refreshResume = async () => {
    if (!canLoadSeekerData()) return null

    const data = await getMyResume()
    setHasResume(!!data.has_resume)
    setResume(data.resume || null)
    return data.resume || null
  }

  const refreshProfile = async () => {
    if (!canLoadSeekerData()) return null

    const data = await getMySeekerProfile()
    setCompleted(!!data.is_complete)
    setProfile(data || null)
    return data || null
  }

  const saveProfile = async (data) => {
    const saved = await saveMySeekerProfile(data)
    setCompleted(!!saved.is_complete)
    setProfile(saved)
    return saved
  }

  useEffect(() => {
    refreshResume().catch(() => {
      setHasResume(false)
      setResume(null)
    })
    refreshProfile().catch(() => {
      setCompleted(false)
      setProfile(null)
    })
  }, [])

  const markCompleted = (nextProfile = null) => {
    setCompleted(true)
    if (nextProfile) setProfile(nextProfile)
  }
  const markResume = (nextResume = null) => {
    setHasResume(true)
    if (nextResume) setResume(nextResume)
  }

  return (
    <ProfileCtx.Provider value={{ completed, hasResume, resume, profile, unlocked, markCompleted, markResume, refreshResume, refreshProfile, saveProfile }}>
      {children}
    </ProfileCtx.Provider>
  )
}

export function useProfile() {
  const ctx = useContext(ProfileCtx)
  if (!ctx) throw new Error('useProfile must be inside ProfileProvider')
  return ctx
}
