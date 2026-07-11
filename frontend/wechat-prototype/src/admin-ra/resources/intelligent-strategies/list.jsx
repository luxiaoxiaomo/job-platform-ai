import React, { useEffect, useState } from 'react'
import { Title, useDataProvider, useNotify } from 'react-admin'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
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
import AddIcon from '@mui/icons-material/Add'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import PlayCircleIcon from '@mui/icons-material/PlayCircle'
import RefreshIcon from '@mui/icons-material/Refresh'
import VisibilityIcon from '@mui/icons-material/Visibility'
import EditIcon from '@mui/icons-material/Edit'
import { useNavigate } from 'react-router-dom'

const emptyFilter = {
  status: '',
  base_rule_config_id: '',
}

const statusChoices = [
  { value: '', label: 'All statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'evaluating', label: 'Evaluating' },
  { value: 'testing', label: 'Testing' },
  { value: 'active', label: 'Active' },
  { value: 'archived', label: 'Archived' },
]

function cleanFilter(filter) {
  return Object.fromEntries(
    Object.entries(filter).filter(([, value]) => value !== undefined && value !== null && value !== '')
  )
}

function chipColor(status) {
  if (status === 'active') return 'success'
  if (status === 'testing' || status === 'evaluating') return 'info'
  if (status === 'archived') return 'warning'
  return 'default'
}

function percent(value) {
  return `${Math.round(Number(value || 0) * 100)}%`
}

function weightSummary(record) {
  const weights = record.hybrid_weights || {}
  return [
    `rule ${percent(weights.rule_score)}`,
    `vector ${percent(weights.vector_score)}`,
    `profile ${percent(weights.profile_coverage_score)}`,
    `behavior ${percent(weights.behavior_quality_score)}`,
  ].join(' / ')
}

export default function IntelligentStrategyList() {
  const dataProvider = useDataProvider()
  const notify = useNotify()
  const navigate = useNavigate()
  const [filter, setFilter] = useState(emptyFilter)
  const [strategies, setStrategies] = useState([])
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [savingId, setSavingId] = useState(null)

  const load = async (nextFilter = filter) => {
    setLoading(true)
    try {
      const [strategyResult, ruleResult] = await Promise.all([
        dataProvider.getList('intelligent-strategies', {
          pagination: { page: 1, perPage: 50 },
          filter: cleanFilter(nextFilter),
        }),
        dataProvider.getList('match-rules', {
          pagination: { page: 1, perPage: 100 },
          filter: {},
        }),
      ])
      setStrategies(strategyResult.data || [])
      setRules(ruleResult.data || [])
    } catch (err) {
      notify(err?.message || 'Failed to load intelligent strategies', { type: 'error' })
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
    await load(emptyFilter)
  }

  const cloneStrategy = async (strategy) => {
    setSavingId(strategy.id)
    try {
      const clone = await dataProvider.cloneIntelligentStrategy(strategy.id, {
        name: `${strategy.name} copy`,
        reason: 'Clone from Intelligent Matching admin page',
      })
      notify('Strategy cloned into draft', { type: 'success' })
      navigate(`/admin-ra/intelligent-matching/strategies/${clone.id}/edit`)
    } catch (err) {
      notify(err?.message || 'Clone strategy failed', { type: 'error' })
    } finally {
      setSavingId(null)
    }
  }

  const runEvaluation = async (strategy) => {
    setSavingId(strategy.id)
    try {
      const report = await dataProvider.runIntelligentEvaluation(strategy.id, {
        sample_set_id: 1,
        sample_source_policy: 'allow_demo_and_mock',
        sample_source_distribution: { seeded_demo: 12, mock_only: 0 },
        notes: 'Quick non-launch evaluation from Intelligent Matching admin page',
      })
      notify(`Evaluation #${report.evaluation_id} completed`, { type: 'success' })
      navigate(`/admin-ra/intelligent-matching/strategies/${strategy.id}?evaluationId=${report.evaluation_id}`)
    } catch (err) {
      notify(err?.message || 'Run Evaluation failed', { type: 'error' })
    } finally {
      setSavingId(null)
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Title title="Intelligent Matching" />
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 2 }}>
        <Box>
          <Typography variant="h6">Intelligent Matching</Typography>
          <Typography variant="body2" color="text.secondary">
            Hybrid strategy drafts, vector recall switches, and offline evaluation evidence.
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => navigate('/admin-ra/intelligent-matching/strategies/create')}>
          Create Draft
        </Button>
      </Box>

      <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 2 }}>
          <TextField select label="Status" value={filter.status} onChange={updateFilter('status')} size="small">
            {statusChoices.map(item => <MenuItem key={item.value || 'all'} value={item.value}>{item.label}</MenuItem>)}
          </TextField>
          <TextField select label="Base Rule" value={filter.base_rule_config_id} onChange={updateFilter('base_rule_config_id')} size="small">
            <MenuItem value="">All base rules</MenuItem>
            {rules.map(rule => <MenuItem key={rule.id} value={rule.id}>{rule.name} V{rule.version}</MenuItem>)}
          </TextField>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
          <Button variant="contained" startIcon={<RefreshIcon />} disabled={loading} onClick={() => load()}>
            Apply
          </Button>
          <Button disabled={loading} onClick={resetFilter}>Reset</Button>
        </Box>
      </Paper>

      <Alert severity="info" sx={{ mb: 2 }}>
        Vector-enabled strategies fall back to audited rule_baseline until a real vector store is connected.
      </Alert>

      {loading && <CircularProgress size={24} />}
      {!loading && (
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Base Rule</TableCell>
              <TableCell>vector_recall_enabled</TableCell>
              <TableCell>Hybrid Weights</TableCell>
              <TableCell>Fallback</TableCell>
              <TableCell>Updated</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {strategies.map(strategy => (
              <TableRow key={strategy.id} hover>
                <TableCell>{strategy.name}</TableCell>
                <TableCell><Chip label={strategy.status} color={chipColor(strategy.status)} size="small" /></TableCell>
                <TableCell>{strategy.base_rule_config_id}</TableCell>
                <TableCell>
                  <Chip
                    label={strategy.vector_recall?.enabled ? 'enabled' : 'disabled'}
                    color={strategy.vector_recall?.enabled ? 'info' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>{weightSummary(strategy)}</TableCell>
                <TableCell>{strategy.fallback_policy}</TableCell>
                <TableCell>{strategy.updated_at ? new Date(strategy.updated_at).toLocaleString('zh-CN') : '-'}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    <Button size="small" startIcon={<VisibilityIcon />} onClick={() => navigate(`/admin-ra/intelligent-matching/strategies/${strategy.id}`)}>
                      View
                    </Button>
                    {['draft', 'evaluating'].includes(strategy.status) && (
                      <Button size="small" startIcon={<EditIcon />} onClick={() => navigate(`/admin-ra/intelligent-matching/strategies/${strategy.id}/edit`)}>
                        Edit
                      </Button>
                    )}
                    <Button size="small" startIcon={<ContentCopyIcon />} disabled={savingId === strategy.id} onClick={() => cloneStrategy(strategy)}>
                      Clone
                    </Button>
                    {['draft', 'evaluating', 'testing'].includes(strategy.status) && (
                      <Button size="small" startIcon={<PlayCircleIcon />} disabled={savingId === strategy.id} onClick={() => runEvaluation(strategy)}>
                        Run Evaluation
                      </Button>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
            {strategies.length === 0 && (
              <TableRow>
                <TableCell colSpan={8}>No intelligent strategies.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </Box>
  )
}