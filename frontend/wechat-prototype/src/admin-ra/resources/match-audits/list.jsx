import React, { useEffect, useState } from 'react'
import { Title, useDataProvider, useNotify } from 'react-admin'
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import FactCheckIcon from '@mui/icons-material/FactCheck'
import RefreshIcon from '@mui/icons-material/Refresh'

const emptyFilter = {
  job_id: '',
  seeker_id: '',
  rule_config_id: '',
  experiment_id: '',
  experiment_bucket: '',
  created_from: '',
  created_to: '',
}

function cleanFilter(filter) {
  return Object.fromEntries(
    Object.entries(filter)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => (key.endsWith('_id') ? [key, Number(value)] : [key, value]))
  )
}

export default function MatchAuditList() {
  const dataProvider = useDataProvider()
  const notify = useNotify()
  const [filter, setFilter] = useState(emptyFilter)
  const [audits, setAudits] = useState([])
  const [selectedAudit, setSelectedAudit] = useState(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)

  const load = async (nextFilter = filter) => {
    setLoading(true)
    try {
      const result = await dataProvider.getMatchAudits({ ...cleanFilter(nextFilter), limit: 50 })
      setAudits(result.data || [])
    } catch (err) {
      notify(err?.message || 'Failed to load match audits', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(emptyFilter)
  }, [])

  const updateFilter = (key) => (event) => {
    setFilter(current => ({ ...current, [key]: event.target.value }))
  }

  const resetFilter = async () => {
    setFilter(emptyFilter)
    setSelectedAudit(null)
    await load(emptyFilter)
  }

  const viewAudit = async (audit) => {
    setSelectedAudit(audit)
    setDetailLoading(true)
    try {
      const detail = await dataProvider.getMatchAudit(audit.id)
      setSelectedAudit(detail)
    } catch (err) {
      notify(err?.message || 'Failed to load audit detail', { type: 'error' })
    } finally {
      setDetailLoading(false)
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Title title="Match Audits" />
      <Typography variant="h6" sx={{ mb: 2 }}>Match Audits</Typography>

      <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 2 }}>
          <TextField label="Job ID" value={filter.job_id} onChange={updateFilter('job_id')} size="small" />
          <TextField label="Seeker ID" value={filter.seeker_id} onChange={updateFilter('seeker_id')} size="small" />
          <TextField label="Rule Config ID" value={filter.rule_config_id} onChange={updateFilter('rule_config_id')} size="small" />
          <TextField label="Experiment ID" value={filter.experiment_id} onChange={updateFilter('experiment_id')} size="small" />
          <TextField label="Bucket" value={filter.experiment_bucket} onChange={updateFilter('experiment_bucket')} select size="small">
            <MenuItem value="">Any</MenuItem>
            <MenuItem value="control">Control</MenuItem>
            <MenuItem value="treatment">Treatment</MenuItem>
          </TextField>
          <TextField label="Created From" value={filter.created_from} onChange={updateFilter('created_from')} size="small" placeholder="2026-06-22T00:00:00" />
          <TextField label="Created To" value={filter.created_to} onChange={updateFilter('created_to')} size="small" placeholder="2026-06-23T00:00:00" />
        </Box>
        <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
          <Button variant="contained" startIcon={<FactCheckIcon />} disabled={loading} onClick={() => load()}>
            Apply
          </Button>
          <Button startIcon={<RefreshIcon />} disabled={loading} onClick={resetFilter}>
            Reset
          </Button>
        </Box>
      </Paper>

      {loading && <CircularProgress size={24} />}
      {!loading && (
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Job</TableCell>
              <TableCell>Seeker</TableCell>
              <TableCell>Rule</TableCell>
              <TableCell>Experiment</TableCell>
              <TableCell>Bucket</TableCell>
              <TableCell>Score</TableCell>
              <TableCell>Level</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {audits.map(audit => (
              <TableRow key={audit.id} hover selected={selectedAudit?.id === audit.id}>
                <TableCell>{audit.id}</TableCell>
                <TableCell>{audit.job?.title || audit.job_id}</TableCell>
                <TableCell>{audit.seeker?.display_name || audit.seeker_id}</TableCell>
                <TableCell>{audit.rule_config ? `${audit.rule_config.name} V${audit.rule_config.version}` : audit.rule_config_id || '-'}</TableCell>
                <TableCell>{audit.experiment?.name || audit.experiment_id || '-'}</TableCell>
                <TableCell>{audit.experiment_bucket || '-'}</TableCell>
                <TableCell>{audit.overall_score}</TableCell>
                <TableCell><Chip label={audit.level} size="small" /></TableCell>
                <TableCell>{audit.created_at ? new Date(audit.created_at).toLocaleString() : '-'}</TableCell>
                <TableCell>
                  <Button size="small" onClick={() => viewAudit(audit)}>Detail</Button>
                </TableCell>
              </TableRow>
            ))}
            {audits.length === 0 && (
              <TableRow>
                <TableCell colSpan={10}>No match audits.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}

      {selectedAudit && (
        <Paper variant="outlined" sx={{ p: 2, mt: 3, borderRadius: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mb: 1 }}>
            <Box>
              <Typography variant="h6">Audit #{selectedAudit.id}</Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedAudit.job?.title || `Job ${selectedAudit.job_id}`} · {selectedAudit.seeker?.display_name || `Seeker ${selectedAudit.seeker_id}`}
              </Typography>
            </Box>
            {detailLoading && <CircularProgress size={22} />}
          </Box>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            <Chip label={`Score ${selectedAudit.overall_score}`} size="small" color="primary" />
            <Chip label={selectedAudit.level} size="small" />
            <Chip label={`Rule ${selectedAudit.rule_config_id || '-'}`} size="small" />
            <Chip label={`Experiment ${selectedAudit.experiment_id || '-'}`} size="small" />
            <Chip label={`Bucket ${selectedAudit.experiment_bucket || '-'}`} size="small" />
          </Box>
          <Typography variant="body2" sx={{ mb: 2 }}>{selectedAudit.recommendation}</Typography>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="subtitle1" sx={{ mb: 1 }}>Dimension Snapshot</Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Dimension</TableCell>
                <TableCell>Score</TableCell>
                <TableCell>Weight</TableCell>
                <TableCell>Weighted</TableCell>
                <TableCell>Matched</TableCell>
                <TableCell>Missing</TableCell>
                <TableCell>Explanation</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(selectedAudit.dimension_scores || []).map(item => (
                <TableRow key={item.key} hover>
                  <TableCell>{item.label || item.key}</TableCell>
                  <TableCell>{item.score}</TableCell>
                  <TableCell>{item.effective_weight ?? item.configured_weight}</TableCell>
                  <TableCell>{item.weighted_score}</TableCell>
                  <TableCell>{Array.isArray(item.matched) ? item.matched.join(', ') || '-' : '-'}</TableCell>
                  <TableCell>{Array.isArray(item.missing) ? item.missing.join(', ') || '-' : '-'}</TableCell>
                  <TableCell>{item.explanation || '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </Box>
  )
}
