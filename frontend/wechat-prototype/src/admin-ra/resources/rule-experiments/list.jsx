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
import AssessmentIcon from '@mui/icons-material/Assessment'
import PauseCircleIcon from '@mui/icons-material/PauseCircle'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import ScienceIcon from '@mui/icons-material/Science'
import StopCircleIcon from '@mui/icons-material/StopCircle'

const emptyForm = {
  name: '',
  description: '',
  scope: 'global',
  template_key: 'default',
  status: 'draft',
  traffic_percent: 10,
  control_config_id: '',
  treatment_config_id: '',
}

export default function RuleExperimentList() {
  const dataProvider = useDataProvider()
  const notify = useNotify()
  const [experiments, setExperiments] = useState([])
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [selectedExperiment, setSelectedExperiment] = useState(null)
  const [effects, setEffects] = useState(null)
  const [audits, setAudits] = useState([])
  const [form, setForm] = useState(emptyForm)

  const load = async () => {
    setLoading(true)
    try {
      const [experimentResult, ruleResult] = await Promise.all([
        dataProvider.getList('rule-experiments', { pagination: { page: 1, perPage: 50 }, filter: {} }),
        dataProvider.getList('match-rules', { pagination: { page: 1, perPage: 50 }, filter: {} }),
      ])
      setExperiments(experimentResult.data || [])
      setRules(ruleResult.data || [])
      const firstRule = ruleResult.data?.[0]
      if (firstRule && !form.control_config_id) {
        setForm(value => ({
          ...value,
          scope: firstRule.scope || 'global',
          template_key: firstRule.template_key || 'default',
          control_config_id: firstRule.id,
          treatment_config_id: firstRule.id,
        }))
      }
    } catch (err) {
      notify(err?.message || 'Failed to load experiments', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const updateForm = (key) => (event) => {
    const value = event.target.value
    setForm(current => ({ ...current, [key]: value }))
    if (key === 'control_config_id') {
      const rule = rules.find(item => String(item.id) === String(value))
      if (rule) {
        setForm(current => ({
          ...current,
          control_config_id: value,
          scope: rule.scope,
          template_key: rule.template_key,
        }))
      }
    }
  }

  const createExperiment = async () => {
    if (!form.name.trim()) {
      notify('Experiment name is required', { type: 'warning' })
      return
    }
    setSaving(true)
    try {
      await dataProvider.create('rule-experiments', {
        data: {
          ...form,
          traffic_percent: Number(form.traffic_percent),
          control_config_id: Number(form.control_config_id),
          treatment_config_id: Number(form.treatment_config_id),
          audience: {},
        },
      })
      notify('Experiment entry created', { type: 'success' })
      setForm(value => ({ ...emptyForm, control_config_id: value.control_config_id, treatment_config_id: value.treatment_config_id }))
      await load()
    } catch (err) {
      notify(err?.message || 'Create experiment failed', { type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const updateExperimentStatus = async (experiment, status) => {
    setSaving(true)
    try {
      await dataProvider.updateRuleExperimentStatus(experiment.id, {
        status,
        reason: `${status} experiment from governance page`,
      })
      notify(`Experiment ${status}`, { type: 'success' })
      await load()
      if (selectedExperiment?.id === experiment.id) {
        const refreshed = experiments.find(item => item.id === experiment.id)
        await viewExperimentEffects(refreshed || experiment)
      }
    } catch (err) {
      notify(err?.message || 'Update experiment status failed', { type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const viewExperimentEffects = async (experiment) => {
    setSelectedExperiment(experiment)
    setDetailLoading(true)
    try {
      const [effectResult, auditResult] = await Promise.all([
        dataProvider.getRuleExperimentEffects(experiment.id),
        dataProvider.getMatchAudits({ experiment_id: experiment.id, limit: 20 }),
      ])
      setEffects(effectResult)
      setAudits(auditResult.data || [])
    } catch (err) {
      notify(err?.message || 'Failed to load experiment effects', { type: 'error' })
      setEffects(null)
      setAudits([])
    } finally {
      setDetailLoading(false)
    }
  }

  const renderBucket = (bucketName) => {
    const bucket = effects?.buckets?.[bucketName] || {}
    return (
      <Paper key={bucketName} variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
        <Typography variant="subtitle2" sx={{ textTransform: 'capitalize', mb: 1 }}>{bucketName}</Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 1 }}>
          <Typography variant="body2">Matches: {bucket.match_count || 0}</Typography>
          <Typography variant="body2">Avg score: {bucket.avg_score ?? '-'}</Typography>
          <Typography variant="body2">High: {bucket.high_count || 0}</Typography>
          <Typography variant="body2">Medium: {bucket.medium_count || 0}</Typography>
          <Typography variant="body2">Low: {bucket.low_count || 0}</Typography>
        </Box>
      </Paper>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      <Title title="Rule AB Tests" />
      <Typography variant="h6" sx={{ mb: 2 }}>Gray / AB Test Entry</Typography>

      <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 2 }}>
          <TextField label="Name" value={form.name} onChange={updateForm('name')} size="small" />
          <TextField label="Description" value={form.description} onChange={updateForm('description')} size="small" />
          <TextField label="Traffic %" type="number" value={form.traffic_percent} onChange={updateForm('traffic_percent')} size="small" inputProps={{ min: 0, max: 100 }} />
          <TextField label="Status" value={form.status} onChange={updateForm('status')} select size="small">
            <MenuItem value="draft">Draft</MenuItem>
            <MenuItem value="running">Running</MenuItem>
            <MenuItem value="paused">Paused</MenuItem>
            <MenuItem value="ended">Ended</MenuItem>
          </TextField>
          <TextField label="Control Rule" value={form.control_config_id} onChange={updateForm('control_config_id')} select size="small">
            {rules.map(rule => (
              <MenuItem key={rule.id} value={rule.id}>
                {rule.name} V{rule.version}
              </MenuItem>
            ))}
          </TextField>
          <TextField label="Treatment Rule" value={form.treatment_config_id} onChange={updateForm('treatment_config_id')} select size="small">
            {rules.map(rule => (
              <MenuItem key={rule.id} value={rule.id}>
                {rule.name} V{rule.version}
              </MenuItem>
            ))}
          </TextField>
        </Box>
        <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
          <Chip label={`Scope: ${form.scope}`} size="small" />
          <Chip label={`Template: ${form.template_key}`} size="small" />
          <Button variant="contained" startIcon={<ScienceIcon />} disabled={saving || loading} onClick={createExperiment}>
            Create Entry
          </Button>
        </Box>
      </Paper>

      {loading && <CircularProgress size={24} />}
      {!loading && (
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Traffic</TableCell>
              <TableCell>Scope</TableCell>
              <TableCell>Template</TableCell>
              <TableCell>Control</TableCell>
              <TableCell>Treatment</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {experiments.map(item => (
              <TableRow key={item.id} hover selected={selectedExperiment?.id === item.id}>
                <TableCell>{item.name}</TableCell>
                <TableCell><Chip label={item.status} size="small" /></TableCell>
                <TableCell>{item.traffic_percent}%</TableCell>
                <TableCell>{item.scope}</TableCell>
                <TableCell>{item.template_key}</TableCell>
                <TableCell>{item.control_config_id}</TableCell>
                <TableCell>{item.treatment_config_id}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    <Button
                      size="small"
                      startIcon={<AssessmentIcon />}
                      onClick={() => viewExperimentEffects(item)}
                    >
                      Effects
                    </Button>
                    {item.status === 'running' && (
                      <Button
                        size="small"
                        startIcon={<PauseCircleIcon />}
                        disabled={saving}
                        onClick={() => updateExperimentStatus(item, 'paused')}
                      >
                        Pause
                      </Button>
                    )}
                    {(item.status === 'draft' || item.status === 'paused') && (
                      <Button
                        size="small"
                        startIcon={<PlayArrowIcon />}
                        disabled={saving}
                        onClick={() => updateExperimentStatus(item, 'running')}
                      >
                        Run
                      </Button>
                    )}
                    {item.status !== 'ended' && (
                      <Button
                        size="small"
                        color="warning"
                        startIcon={<StopCircleIcon />}
                        disabled={saving}
                        onClick={() => updateExperimentStatus(item, 'ended')}
                      >
                        End
                      </Button>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
            {experiments.length === 0 && (
              <TableRow>
                <TableCell colSpan={8}>No experiment entries.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}

      {selectedExperiment && (
        <Paper variant="outlined" sx={{ p: 2, mt: 3, borderRadius: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 2 }}>
            <Box>
              <Typography variant="h6">{selectedExperiment.name}</Typography>
              <Typography variant="body2" color="text.secondary">
                Effects and match audit trail for experiment #{selectedExperiment.id}
              </Typography>
            </Box>
            <Button
              size="small"
              startIcon={<AssessmentIcon />}
              onClick={() => viewExperimentEffects(selectedExperiment)}
              disabled={detailLoading}
            >
              Refresh
            </Button>
          </Box>

          {detailLoading && <CircularProgress size={24} />}
          {!detailLoading && (
            <>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 2, mb: 2 }}>
                {renderBucket('control')}
                {renderBucket('treatment')}
              </Box>

              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle1" sx={{ mb: 1 }}>Recent Match Audits</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Bucket</TableCell>
                    <TableCell>Rule</TableCell>
                    <TableCell>Job</TableCell>
                    <TableCell>Score</TableCell>
                    <TableCell>Level</TableCell>
                    <TableCell>Created</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {audits.map(audit => (
                    <TableRow key={audit.id} hover>
                      <TableCell>{audit.id}</TableCell>
                      <TableCell>{audit.experiment_bucket || '-'}</TableCell>
                      <TableCell>{audit.rule_config_id || '-'}</TableCell>
                      <TableCell>{audit.job_id}</TableCell>
                      <TableCell>{audit.overall_score}</TableCell>
                      <TableCell><Chip label={audit.level} size="small" /></TableCell>
                      <TableCell>{audit.created_at ? new Date(audit.created_at).toLocaleString() : '-'}</TableCell>
                    </TableRow>
                  ))}
                  {audits.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7}>No audit records yet.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </>
          )}
        </Paper>
      )}
    </Box>
  )
}
