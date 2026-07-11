import React, { useEffect, useMemo, useState } from 'react'
import { Title, useDataProvider, useNotify } from 'react-admin'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControlLabel,
  MenuItem,
  Paper,
  Switch,
  TextField,
  Typography,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import SaveIcon from '@mui/icons-material/Save'
import { useNavigate, useParams } from 'react-router-dom'

const defaultForm = {
  name: '',
  description: '',
  base_rule_config_id: '',
  vector_recall_enabled: false,
  vector_recall_top_n: 100,
  vector_recall_min_similarity: 0.62,
  vector_recall_candidate_source: 'job_resume_profile',
  rule_score: 0.7,
  vector_score: 0.2,
  profile_coverage_score: 0.1,
  behavior_quality_score: 0,
  fallback_policy: 'rule_baseline',
}

function toForm(record) {
  const vectorRecall = record.vector_recall || {}
  const hybridWeights = record.hybrid_weights || {}
  return {
    name: record.name || '',
    description: record.description || '',
    base_rule_config_id: record.base_rule_config_id || '',
    vector_recall_enabled: Boolean(vectorRecall.enabled),
    vector_recall_top_n: vectorRecall.top_n ?? 100,
    vector_recall_min_similarity: vectorRecall.min_similarity ?? 0.62,
    vector_recall_candidate_source: vectorRecall.candidate_source || 'job_resume_profile',
    rule_score: hybridWeights.rule_score ?? 0.7,
    vector_score: hybridWeights.vector_score ?? 0.2,
    profile_coverage_score: hybridWeights.profile_coverage_score ?? 0.1,
    behavior_quality_score: hybridWeights.behavior_quality_score ?? 0,
    fallback_policy: record.fallback_policy || 'rule_baseline',
  }
}

function weightTotal(form) {
  return ['rule_score', 'vector_score', 'profile_coverage_score', 'behavior_quality_score']
    .reduce((sum, key) => sum + Number(form[key] || 0), 0)
}

export default function IntelligentStrategyForm({ mode = 'create' }) {
  const { id } = useParams()
  const dataProvider = useDataProvider()
  const notify = useNotify()
  const navigate = useNavigate()
  const [rules, setRules] = useState([])
  const [strategy, setStrategy] = useState(null)
  const [form, setForm] = useState(defaultForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const readOnly = mode === 'edit' && strategy && !['draft', 'evaluating'].includes(strategy.status)
  const total = useMemo(() => weightTotal(form), [form])
  const totalValid = Math.abs(total - 1) <= 0.001

  const load = async () => {
    setLoading(true)
    try {
      const ruleResult = await dataProvider.getList('match-rules', {
        pagination: { page: 1, perPage: 100 },
        filter: {},
      })
      setRules(ruleResult.data || [])
      if (mode === 'edit') {
        const result = await dataProvider.getOne('intelligent-strategies', { id })
        setStrategy(result.data)
        setForm(toForm(result.data))
      } else if (ruleResult.data?.[0]) {
        setForm(current => ({ ...current, base_rule_config_id: ruleResult.data[0].id }))
      }
    } catch (err) {
      notify(err?.message || 'Failed to load strategy form', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [id, mode])

  const updateField = (key) => (event) => {
    setForm(current => ({ ...current, [key]: event.target.value }))
  }

  const updateBoolean = (key) => (event) => {
    setForm(current => ({ ...current, [key]: event.target.checked }))
  }

  const save = async () => {
    if (readOnly) return
    if (!form.name.trim()) {
      notify('Strategy name is required', { type: 'warning' })
      return
    }
    if (!form.base_rule_config_id) {
      notify('base_rule_config_id is required', { type: 'warning' })
      return
    }
    if (!totalValid) {
      notify('hybrid_weights_total_must_equal_1', { type: 'warning' })
      return
    }
    setSaving(true)
    try {
      const result = mode === 'edit'
        ? await dataProvider.update('intelligent-strategies', { id, data: form, previousData: strategy })
        : await dataProvider.create('intelligent-strategies', { data: form })
      notify(mode === 'edit' ? 'Strategy updated' : 'Strategy draft created', { type: 'success' })
      navigate(`/admin-ra/intelligent-matching/strategies/${result.data.id}`)
    } catch (err) {
      notify(err?.message || 'Save intelligent strategy failed', { type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const cloneIntoDraft = async () => {
    if (!strategy) return
    setSaving(true)
    try {
      const clone = await dataProvider.cloneIntelligentStrategy(strategy.id, {
        name: `${strategy.name} draft`,
        reason: 'Clone into Draft from intelligent strategy form',
      })
      notify('Clone into Draft created', { type: 'success' })
      navigate(`/admin-ra/intelligent-matching/strategies/${clone.id}/edit`)
    } catch (err) {
      notify(err?.message || 'Clone into Draft failed', { type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Title title={mode === 'edit' ? 'Edit Intelligent Strategy' : 'Create Intelligent Strategy'} />
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 2 }}>
        <Box>
          <Typography variant="h6">{mode === 'edit' ? 'Edit Intelligent Strategy' : 'Create Draft'}</Typography>
          <Typography variant="body2" color="text.secondary">
            Configure hybrid weights and vector recall boundaries for runtime matching.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/admin-ra/intelligent-matching/strategies')}>
            Back
          </Button>
          {strategy && (
            <Button startIcon={<ContentCopyIcon />} disabled={saving} onClick={cloneIntoDraft}>
              Clone into Draft
            </Button>
          )}
          <Button variant="contained" startIcon={<SaveIcon />} disabled={saving || loading || readOnly} onClick={save}>
            Save
          </Button>
        </Box>
      </Box>

      {loading && <CircularProgress size={24} />}
      {!loading && (
        <>
          {readOnly && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              This strategy is not editable in its current status. Clone it into a draft before changing weights.
            </Alert>
          )}

          <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2 }}>
            <Typography variant="subtitle1" sx={{ mb: 2 }}>Strategy Identity</Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 2 }}>
              <TextField label="Name" value={form.name} onChange={updateField('name')} size="small" inputProps={{ readOnly }} />
              <TextField select label="base_rule_config_id" value={form.base_rule_config_id} onChange={updateField('base_rule_config_id')} size="small" disabled={readOnly}>
                {rules.map(rule => <MenuItem key={rule.id} value={rule.id}>{rule.name} V{rule.version} · #{rule.id}</MenuItem>)}
              </TextField>
              <TextField label="Fallback Policy" value={form.fallback_policy} onChange={updateField('fallback_policy')} size="small" inputProps={{ readOnly: true }} />
              {strategy && <Chip label={`Status: ${strategy.status}`} sx={{ justifySelf: 'start', alignSelf: 'center' }} />}
            </Box>
            <TextField
              label="Description"
              value={form.description}
              onChange={updateField('description')}
              size="small"
              multiline
              minRows={2}
              fullWidth
              sx={{ mt: 2 }}
              inputProps={{ readOnly }}
            />
          </Paper>

          <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2 }}>
            <Typography variant="subtitle1" sx={{ mb: 2 }}>Vector Recall</Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 2 }}>
              <FormControlLabel
                control={<Switch checked={form.vector_recall_enabled} onChange={updateBoolean('vector_recall_enabled')} disabled={readOnly} />}
                label="vector_recall_enabled"
              />
              <TextField label="Top N" type="number" value={form.vector_recall_top_n} onChange={updateField('vector_recall_top_n')} size="small" inputProps={{ min: 1, max: 500, readOnly }} />
              <TextField label="Min Similarity" type="number" value={form.vector_recall_min_similarity} onChange={updateField('vector_recall_min_similarity')} size="small" inputProps={{ min: 0, max: 1, step: 0.01, readOnly }} />
              <TextField label="Candidate Source" value={form.vector_recall_candidate_source} onChange={updateField('vector_recall_candidate_source')} size="small" inputProps={{ readOnly }} />
            </Box>
          </Paper>

          <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 2 }}>
              <Typography variant="subtitle1">Hybrid Weights</Typography>
              <Chip label={`Total ${total.toFixed(3)}`} color={totalValid ? 'success' : 'warning'} size="small" />
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 2 }}>
              <TextField label="rule_score" type="number" value={form.rule_score} onChange={updateField('rule_score')} size="small" inputProps={{ min: 0, max: 1, step: 0.01, readOnly }} />
              <TextField label="vector_score" type="number" value={form.vector_score} onChange={updateField('vector_score')} size="small" inputProps={{ min: 0, max: 1, step: 0.01, readOnly }} />
              <TextField label="profile_coverage_score" type="number" value={form.profile_coverage_score} onChange={updateField('profile_coverage_score')} size="small" inputProps={{ min: 0, max: 1, step: 0.01, readOnly }} />
              <TextField label="behavior_quality_score" type="number" value={form.behavior_quality_score} onChange={updateField('behavior_quality_score')} size="small" inputProps={{ min: 0, max: 1, step: 0.01, readOnly }} />
            </Box>
          </Paper>
        </>
      )}
    </Box>
  )
}