import { useEffect, useState } from 'react'
import { listPublicTagLibraryItems } from '../services/baseData.js'

export function usePublicTagOptions(limit = 100) {
  const [tagOptions, setTagOptions] = useState([])
  const [tagOptionsLoading, setTagOptionsLoading] = useState(false)

  useEffect(() => {
    let alive = true
    setTagOptionsLoading(true)
    listPublicTagLibraryItems({ limit })
      .then(data => {
        if (alive) setTagOptions(data.items || [])
      })
      .catch(() => {
        if (alive) setTagOptions([])
      })
      .finally(() => {
        if (alive) setTagOptionsLoading(false)
      })
    return () => { alive = false }
  }, [limit])

  return { tagOptions, tagOptionsLoading }
}

export function pickPublicTagNames(tagOptions, seed = 0, count = 3) {
  if (!Array.isArray(tagOptions) || tagOptions.length === 0) return []
  const offset = Math.abs(Number(seed) || 0) % tagOptions.length
  const names = []
  for (let index = 0; index < Math.min(count, tagOptions.length); index += 1) {
    const tag = tagOptions[(offset + index) % tagOptions.length]
    if (tag?.name) names.push(tag.name)
  }
  return names
}
