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
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import EditIcon from '@mui/icons-material/Edit'
import PlayCircleIcon from '@mui/icons-material/PlayCircle'
import RefreshIcon from '@mui/icons-material/Refresh'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

const defaultEvaluationForm = {
  sample_set_id: 1,
  sample_source_policy: 'allow_real_and_manual_only',
  real_behavior: 30,
  manual_review: 10,
  seeded_demo: 0,
  mock_only: 0,
  notes: '',
}

function chipColor(value) {
  if (value === 'active' || value === 'eligible_for_gray') return 'success'
  if (value === 'testing' || value === 'evaluating') return 'info'
  if (value === 'demo_only' || value === 'insufficient_sample' || value === 'archived') return 'warning'
  return 'default'
}

function metricRows(metrics = {}) {
  return Object.entries(metrics).map(([key, value]) => ({ key, value }))
}

function JsonBlock({ value }) {
  return (
    <Box component="pre" sx={{ m: 0, p: 1.5, bgcolor: '#f6f7f9', borderRadius: 1, overflow: 'auto', fontSize: 12 }}>
      {JSON.stringify(value || {}, null, 2)}
    </Box>
  )
}

export default function IntelligentStrategyShow() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const dataProvider = useDataProvider()
  const notify = useNotify()
  const [strategy, setStrategy] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [form, setForm] = useState(defaultEvaluationForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const queryEvaluationId = new URLSearchParams(location.search).get('evaluationId')
  const canEvaluate = strategy && ['draft', 'evaluating', 'testing'].includes(strategy.status)

  const load = async () => {
    setLoading(true)
    try {
      const result = await dataProvider.getOne('intelligent-strategies', { id })
      setStrategy(result.data)
      if (queryEvaluationId) {
        const report = await dataProvider.getIntelligentEvaluation(queryEvaluationId)
        setEvaluation(report)
      }
    } catch (err) {
      notify(err?.message || 'Failed to load intelligent strategy', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [id, queryEvaluationId])

  const updateForm = (key) => (event) => {
    setForm(current => ({ ...current, [key]: event.target.value }))
  }

  const cloneIntoDraft = async () => {
    if (!strategy) return
    setSaving(true)
    try {
      const clone = await dataProvider.cloneIntelligentStrategy(strategy.id, {
        name: `${strategy.name} draft`,
        reason: 'Clone into Draft from intelligent strategy detail',
      })
      notify('Clone into Draft created', { type: 'success' })
      navigate(`/admin-ra/intelligent-matching/strategies/${clone.id}/edit`)
    } catch (err) {
      notify(err?.message || 'Clone into Draft failed', { type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const runEvaluation = async () => {
    if (!canEvaluate) return
    setSaving(true)
    try {
      const payload = {
        sample_set_id: Number(form.sample_set_id),
        sample_source_policy: form.sample_source_policy,
        sample_source_distribution: {
          real_behavior: Number(form.real_behavior || 0),
          manual_review: Number(form.manual_review || 0),
          seeded_demo: Number(form.seeded_demo || 0),
          mock_only: Number(form.mock_only || 0),
        },
        notes: form.notes,
      }
      const report = await dataProvider.runIntelligentEvaluation(strategy.id, payload)
      setEvaluation(report)
      notify(`Evaluation #${report.evaluation_id} completed`, { type: 'success' })
      navigate(`/admin-ra/intelligent-matching/strategies/${strategy.id}?evaluationId=${report.evaluation_id}`, { replace: true })
    } catch (err) {
      notify(err?.message || 'Run Evaluation failed', { type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Title title="Intelligent Strategy" />
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 2 }}>
        <Box>
          <Typography variant="h6">Intelligent Strategy</Typography>
          <Typography variant="body2" color="text.secondary">
            Runtime hybrid scoring configuration and offline evaluation report.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/admin-ra/intelligent-matching/strategies')}>Back</Button>
          {strategy && ['draft', 'evaluating'].includes(strategy.status) && (
            <Button startIcon={<EditIcon />} onClick={() => navigate(`/admin-ra/intelligent-matching/strategies/${strategy.id}/edit`)}>Edit</Button>
          )}
          {strategy && <Button startIcon={<ContentCopyIcon />} disabled={saving} onClick={cloneIntoDraft}>Clone into Draft</Button>}
          <Button startIcon={<RefreshIcon />} disabled={loading} onClick={load}>Refresh</Button>
        </Box>
      </Box>

      {loading && <CircularProgress size={24} />}
      {!loading && strategy && (
        <>
          <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 2 }}>
              <Box>
                <Typography variant="h6">{strategy.name}</Typography>
                <Typography variant="body2" color="text.secondary">#{strategy.id} · Base rule #{strategy.base_rule_config_id}</Typography>
              </Box>
              <Chip label={strategy.status} color={chipColor(strategy.status)} />
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 2 }}>
              <Box><Typography variant="caption" color="text.secondary">Fallback</Typography><Typography>{strategy.fallback_policy}</Typography></Box>
              <Box><Typography variant="caption" color="text.secondary">Vector Recall</Typography><Typography>{strategy.vector_recall?.enabled ? 'enabled' : 'disabled'}</Typography></Box>
              <Box><Typography variant="caption" color="text.secondary">Created</Typography><Typography>{strategy.created_at ? new Date(strategy.created_at).toLocaleString('zh-CN') : '-'}</Typography></Box>
              <Box><Typography variant="caption" color="text.secondary">Updated</Typography><Typography>{strategy.updated_at ? new Date(strategy.updated_at).toLocaleString('zh-CN') : '-'}</Typography></Box>
            </Box>
            {strategy.description && <Typography variant="body2" sx={{ mt: 2 }}>{strategy.description}</Typography>}
          </Paper>

          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 2, mb: 3 }}>
            <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>Vector Recall Config</Typography>
              <JsonBlock value={strategy.vector_recall} />
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>Hybrid Weights</Typography>
              <JsonBlock value={strategy.hybrid_weights} />
            </Paper>
          </Box>

          <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 2 }}>
              <Box>
                <Typography variant="subtitle1">Offline Evaluation</Typography>
                <Typography variant="body2" color="text.secondary">Non-launch evidence for local comparison and governance review.</Typography>
              </Box>
              <Button variant="contained" startIcon={<PlayCircleIcon />} disabled={!canEvaluate || saving} onClick={runEvaluation}>
                Run Evaluation
              </Button>
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 2 }}>
              <TextField label="Sample Set ID" type="number" value={form.sample_set_id} onChange={updateForm('sample_set_id')} size="small" />
              <TextField select label="Policy" value={form.sample_source_policy} onChange={updateForm('sample_source_policy')} size="small">
                <MenuItem value="allow_real_and_manual_only">Real + manual only</MenuItem>
                <MenuItem value="allow_demo_and_mock">Allow demo/mock</MenuItem>
              </TextField>
              <TextField label="real_behavior" type="number" value={form.real_behavior} onChange={updateForm('real_behavior')} size="small" />
              <TextField label="manual_review" type="number" value={form.manual_review} onChange={updateForm('manual_review')} size="small" />
              <TextField label="seeded_demo" type="number" value={form.seeded_demo} onChange={updateForm('seeded_demo')} size="small" />
              <TextField label="mock_only" type="number" value={form.mock_only} onChange={updateForm('mock_only')} size="small" />
              <TextField label="Notes" value={form.notes} onChange={updateForm('notes')} size="small" />
            </Box>
          </Paper>

          {evaluation && (
            <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
              <Alert severity="warning" sx={{ mb: 2 }}>Non-launch evidence: demo/mock samples cannot support production rollout decisions.</Alert>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 2 }}>
                <Box>
                  <Typography variant="subtitle1">Evaluation #{evaluation.evaluation_id}</Typography>
                  <Typography variant="body2" color="text.secondary">sample_source_distribution: {JSON.stringify(evaluation.sample_source_distribution)}</Typography>
                </Box>
                <Chip label={`Decision status: ${evaluation.decision_status}`} color={chipColor(evaluation.decision_status)} />
              </Box>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 2, mb: 2 }}>
                <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>Baseline</Typography>
                  <Table size="small">
                    <TableBody>
                      {metricRows(evaluation.baseline).map(row => <TableRow key={row.key}><TableCell>{row.key}</TableCell><TableCell>{String(row.value)}</TableCell></TableRow>)}
                    </TableBody>
                  </Table>
                </Paper>
                <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>Hybrid</Typography>
                  <Table size="small">
                    <TableBody>
                      {metricRows(evaluation.hybrid).map(row => <TableRow key={row.key}><TableCell>{row.key}</TableCell><TableCell>{String(row.value)}</TableCell></TableRow>)}
                    </TableBody>
                  </Table>
                </Paper>
              </Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Risk Notes</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow><TableCell>Note</TableCell></TableRow>
                </TableHead>
                <TableBody>
                  {(evaluation.risk_notes || []).map(note => <TableRow key={note}><TableCell>{note}</TableCell></TableRow>)}
                  {(evaluation.risk_notes || []).length === 0 && <TableRow><TableCell>No risk notes.</TableCell></TableRow>}
                </TableBody>
              </Table>
            </Paper>
          )}
        </>
      )}
    </Box>
  )
}