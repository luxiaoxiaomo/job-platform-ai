import React, { useEffect, useState } from 'react'
import { Title, useDataProvider, useNotify } from 'react-admin'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  FormControlLabel,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import PublishedWithChangesIcon from '@mui/icons-material/PublishedWithChanges'
import RefreshIcon from '@mui/icons-material/Refresh'
import { useNavigate, useParams } from 'react-router-dom'

const statusColor = {
  active: 'success',
  testing: 'info',
  draft: 'default',
  archived: 'warning',
}

function CheckList({ title, items, severity }) {
  if (!items?.length) {
    return <Alert severity="success" sx={{ mb: 1 }}>{title}: none</Alert>
  }
  return (
    <Box sx={{ display: 'grid', gap: 1 }}>
      {items.map((item, index) => (
        <Alert key={`${item.code}-${index}`} severity={severity}>
          <strong>{item.code}</strong> {item.message}
        </Alert>
      ))}
    </Box>
  )
}

export default function MatchRuleRelease() {
  const { id } = useParams()
  const navigate = useNavigate()
  const notify = useNotify()
  const dataProvider = useDataProvider()
  const [rule, setRule] = useState(null)
  const [releaseCheck, setReleaseCheck] = useState(null)
  const [audits, setAudits] = useState([])
  const [reason, setReason] = useState('Publish rule version')
  const [confirmWarnings, setConfirmWarnings] = useState(true)
  const [loading, setLoading] = useState(true)
  const [publishing, setPublishing] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [ruleResult, checkResult, auditResult] = await Promise.all([
        dataProvider.getOne('match-rules', { id }),
        dataProvider.getRuleReleaseCheck(id),
        dataProvider.getRuleOperationAudits({ resource_type: 'rule_config', resource_id: id, limit: 20 }),
      ])
      setRule(ruleResult.data)
      setReleaseCheck(checkResult)
      setAudits(auditResult.data || [])
    } catch (err) {
      notify(err?.message || 'Failed to load release governance', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [id])

  const publish = async () => {
    if (!reason.trim()) {
      notify('Release reason is required', { type: 'warning' })
      return
    }
    setPublishing(true)
    try {
      const response = await dataProvider.publishRuleConfig(id, {
        reason,
        confirm_warnings: confirmWarnings,
      })
      notify('Rule published', { type: 'success' })
      navigate(`/admin-ra/match-rules/${response.config.id}/show`)
    } catch (err) {
      notify(err?.message || 'Publish failed', { type: 'error' })
      await load()
    } finally {
      setPublishing(false)
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Title title="Rule Release Governance" />
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(`/admin-ra/match-rules/${id}/show`)}>
            Back
          </Button>
          <Typography variant="h6">Release Governance</Typography>
          {rule && <Chip label={rule.status} color={statusColor[rule.status] || 'default'} size="small" />}
        </Box>
        <Button startIcon={<RefreshIcon />} onClick={load} disabled={loading}>
          Refresh
        </Button>
      </Box>

      {loading && <CircularProgress size={24} />}
      {!loading && rule && releaseCheck && (
        <>
          <Paper variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 2 }}>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>{rule.name} V{rule.version}</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              <Chip label={`Scope: ${rule.scope}`} size="small" />
              <Chip label={`Template: ${rule.template_key}`} size="small" />
              <Chip label={`Current active: ${releaseCheck.current_active_config_id || '-'}`} size="small" />
              <Chip
                label={releaseCheck.can_publish ? 'Can publish' : 'Blocked'}
                size="small"
                color={releaseCheck.can_publish ? 'success' : 'error'}
              />
            </Box>
            <CheckList title="Blockers" items={releaseCheck.blockers} severity="error" />
            <Box sx={{ mt: 1 }}>
              <CheckList title="Warnings" items={releaseCheck.warnings} severity="warning" />
            </Box>
          </Paper>

          <Paper variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 2 }}>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>Publish</Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'minmax(220px, 1fr) auto', gap: 2, alignItems: 'center' }}>
              <TextField
                label="Reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                size="small"
                fullWidth
              />
              <FormControlLabel
                control={<Checkbox checked={confirmWarnings} onChange={(event) => setConfirmWarnings(event.target.checked)} />}
                label="Confirm warnings"
              />
            </Box>
            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                startIcon={<PublishedWithChangesIcon />}
                disabled={publishing || !releaseCheck.can_publish}
                onClick={publish}
              >
                Publish Active
              </Button>
            </Box>
          </Paper>

          <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>Operation Audits</Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Actor</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Created</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {audits.map(item => (
                  <TableRow key={item.id} hover>
                    <TableCell>{item.id}</TableCell>
                    <TableCell><Chip label={item.action} size="small" /></TableCell>
                    <TableCell>{item.actor_id || '-'}</TableCell>
                    <TableCell>{item.reason || '-'}</TableCell>
                    <TableCell>{item.created_at ? new Date(item.created_at).toLocaleString() : '-'}</TableCell>
                  </TableRow>
                ))}
                {audits.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5}>No operation audit records.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Paper>
        </>
      )}
    </Box>
  )
}
