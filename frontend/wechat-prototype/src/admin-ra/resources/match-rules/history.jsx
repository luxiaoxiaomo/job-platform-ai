import React, { useEffect, useState } from 'react'
import { Link, Title, useDataProvider, useNotify } from 'react-admin'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import CompareArrowsIcon from '@mui/icons-material/CompareArrows'
import RestoreIcon from '@mui/icons-material/Restore'

const STATUS_META = {
  active: { label: 'Active', color: '#07C160' },
  draft: { label: 'Draft', color: '#999' },
  testing: { label: 'Testing', color: '#1187D6' },
  archived: { label: 'Archived', color: '#FA9D3B' },
}

export default function MatchRuleHistory() {
  const { id } = useParams()
  const navigate = useNavigate()
  const dataProvider = useDataProvider()
  const notify = useNotify()
  const [versions, setVersions] = useState([])
  const [loading, setLoading] = useState(true)
  const [rollingBackId, setRollingBackId] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    dataProvider
      .getManyReference('match-rules', { id, target: 'history' })
      .then(({ data }) => {
        if (!alive) return
        setVersions([...(data || [])].sort((a, b) => (b.version || 0) - (a.version || 0)))
        setError('')
      })
      .catch((err) => {
        if (!alive) return
        setError(err?.message || 'Failed to load history')
        notify(err?.message || 'Failed to load history', { type: 'error' })
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [dataProvider, id, notify])

  const handleRollback = async (target) => {
    const ok = window.confirm(`Create a new active version from V${target.version}?`)
    if (!ok) return
    setRollingBackId(target.id)
    try {
      const response = await dataProvider.rollbackRuleConfig(id, {
        target_config_id: target.id,
        status: 'active',
        name: `Rollback to V${target.version}`,
      })
      notify('Rollback version created', { type: 'success' })
      navigate(`/admin-ra/match-rules/${response.config.id}/show`)
    } catch (err) {
      notify(err?.message || 'Rollback failed', { type: 'error' })
    } finally {
      setRollingBackId(null)
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Title title="Rule Version History" />
      <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(`/admin-ra/match-rules/${id}/show`)}>
          Back
        </Button>
        <Typography variant="h6" sx={{ ml: 2 }}>Rule #{id} History</Typography>
      </Box>

      {loading && <CircularProgress size={24} />}
      {error && <Typography color="error">{error}</Typography>}
      {!loading && !error && versions.length === 0 && (
        <Typography color="textSecondary">No history records.</Typography>
      )}

      {!loading && versions.length > 0 && (
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Version</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Template</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Scope</TableCell>
              <TableCell>Dimensions</TableCell>
              <TableCell>Updated</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {versions.map((version) => {
              const meta = STATUS_META[version.status] || { label: version.status, color: '#999' }
              return (
                <TableRow key={version.id} hover>
                  <TableCell>V{version.version ?? '-'}</TableCell>
                  <TableCell>{version.name}</TableCell>
                  <TableCell>{version.template_name || version.template_key}</TableCell>
                  <TableCell>
                    <Chip label={meta.label} size="small" sx={{ color: meta.color, borderColor: meta.color }} variant="outlined" />
                  </TableCell>
                  <TableCell>{version.scope}</TableCell>
                  <TableCell>{version.dimensions?.length ?? 0}</TableCell>
                  <TableCell>{version.updated_at ? new Date(version.updated_at).toLocaleString('zh-CN') : '-'}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                      <Link to={`/admin-ra/match-rules/${version.id}/show`}>View</Link>
                      {String(version.id) !== String(id) && (
                        <Button
                          size="small"
                          startIcon={<CompareArrowsIcon />}
                          onClick={() => navigate(`/admin-ra/match-rules/${id}/compare/${version.id}`)}
                        >
                          Compare
                        </Button>
                      )}
                      {String(version.id) !== String(id) && (
                        <Button
                          size="small"
                          startIcon={<RestoreIcon />}
                          disabled={rollingBackId === version.id}
                          onClick={() => handleRollback(version)}
                        >
                          Rollback
                        </Button>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      )}
    </Box>
  )
}
