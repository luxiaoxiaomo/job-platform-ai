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
import QueryStatsIcon from '@mui/icons-material/QueryStats'
import RefreshIcon from '@mui/icons-material/Refresh'

const emptyFilter = {
  rule_config_id: '',
  experiment_id: '',
  scope: '',
  template_key: '',
  city: '',
  position_category: '',
  standard_position_id: '',
  job_tag: '',
  segment_type: '',
  created_from: '',
  created_to: '',
}

const segmentTypes = [
  { value: '', label: 'All Segments' },
  { value: 'city', label: 'City' },
  { value: 'position_category', label: 'Position Category' },
  { value: 'standard_position', label: 'Standard Position' },
  { value: 'job_tag', label: 'Job Tag' },
  { value: 'rule_version', label: 'Rule Version' },
  { value: 'experiment_bucket', label: 'Experiment Bucket' },
]

function cleanFilter(filter) {
  return Object.fromEntries(
    Object.entries(filter)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => (key.endsWith('_id') ? [key, Number(value)] : [key, value]))
  )
}

function formatRate(value) {
  return `${Number(value || 0).toFixed(2)}%`
}

function metricValue(value) {
  return value ?? '-'
}

function chipColor(value) {
  if (value === 'high' || value === 'treatment_likely_worse') return 'error'
  if (value === 'medium' || value === 'limited' || value === 'insufficient_sample') return 'warning'
  if (value === 'usable' || value === 'treatment_likely_better') return 'success'
  return 'default'
}

function KpiCard({ label, value, helper }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, borderRadius: 2, minHeight: 92 }}>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>{label}</Typography>
      <Typography variant="h5">{value}</Typography>
      {helper && <Typography variant="caption" color="text.secondary">{helper}</Typography>}
    </Paper>
  )
}

function SectionTitle({ children }) {
  return <Typography variant="subtitle1" sx={{ mb: 1, mt: 1 }}>{children}</Typography>
}

function MetricCells({ item }) {
  return (
    <>
      <TableCell>{item.match_count || 0}</TableCell>
      <TableCell>{metricValue(item.avg_score)}</TableCell>
      <TableCell>{item.high_count || 0}</TableCell>
      <TableCell>{item.medium_count || 0}</TableCell>
      <TableCell>{item.low_count || 0}</TableCell>
      <TableCell>{formatRate(item.low_score_rate)}</TableCell>
      <TableCell>{item.visit_count || 0}</TableCell>
      <TableCell>{item.favorite_count || 0}</TableCell>
      <TableCell>{item.application_count || 0}</TableCell>
      <TableCell>{formatRate(item.application_rate)}</TableCell>
    </>
  )
}

export default function MatchQualityDashboard() {
  const dataProvider = useDataProvider()
  const notify = useNotify()
  const [filter, setFilter] = useState(emptyFilter)
  const [quality, setQuality] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = async (nextFilter = filter) => {
    setLoading(true)
    try {
      const result = await dataProvider.getMatchQualitySummary(cleanFilter(nextFilter))
      setQuality(result)
    } catch (err) {
      notify(err?.message || 'Failed to load match quality summary', { type: 'error' })
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

  const summary = quality?.summary || {}
  const buckets = quality?.experiment_buckets || {}
  const confidence = quality?.experiment_confidence

  return (
    <Box sx={{ p: 3 }}>
      <Title title="Match Quality" />
      <Typography variant="h6" sx={{ mb: 2 }}>Match Quality</Typography>

      <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 2 }}>
          <TextField label="Rule Config ID" value={filter.rule_config_id} onChange={updateFilter('rule_config_id')} size="small" />
          <TextField label="Experiment ID" value={filter.experiment_id} onChange={updateFilter('experiment_id')} size="small" />
          <TextField label="Scope" value={filter.scope} onChange={updateFilter('scope')} size="small" placeholder="global" />
          <TextField label="Template" value={filter.template_key} onChange={updateFilter('template_key')} size="small" placeholder="default" />
          <TextField label="City" value={filter.city} onChange={updateFilter('city')} size="small" />
          <TextField label="Position Category" value={filter.position_category} onChange={updateFilter('position_category')} size="small" />
          <TextField label="Standard Position ID" value={filter.standard_position_id} onChange={updateFilter('standard_position_id')} size="small" />
          <TextField label="Job Tag" value={filter.job_tag} onChange={updateFilter('job_tag')} size="small" />
          <TextField select label="Segment" value={filter.segment_type} onChange={updateFilter('segment_type')} size="small">
            {segmentTypes.map(item => <MenuItem key={item.value || 'all'} value={item.value}>{item.label}</MenuItem>)}
          </TextField>
          <TextField label="Created From" value={filter.created_from} onChange={updateFilter('created_from')} size="small" placeholder="2026-06-22T00:00:00" />
          <TextField label="Created To" value={filter.created_to} onChange={updateFilter('created_to')} size="small" placeholder="2026-06-23T00:00:00" />
        </Box>
        <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
          <Button variant="contained" startIcon={<QueryStatsIcon />} disabled={loading} onClick={() => load()}>
            Apply
          </Button>
          <Button startIcon={<RefreshIcon />} disabled={loading} onClick={resetFilter}>
            Reset
          </Button>
        </Box>
      </Paper>

      {loading && <CircularProgress size={24} />}

      {!loading && (
        <>
          <Alert severity="info" sx={{ mb: 2 }}>
            Behavior metrics can lag behind match audits. Confidence is a business-threshold hint, not a statistical test.
          </Alert>

          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 2, mb: 3 }}>
            <KpiCard label="Matches" value={summary.match_count || 0} helper={`Avg score ${metricValue(summary.avg_score)}`} />
            <KpiCard label="High / Medium / Low" value={`${summary.high_count || 0} / ${summary.medium_count || 0} / ${summary.low_count || 0}`} />
            <KpiCard label="Low Score Rate" value={formatRate(summary.low_score_rate)} helper={summary.sample_status || 'insufficient'} />
            <KpiCard label="Applications" value={summary.application_count || 0} helper={formatRate(summary.application_rate)} />
            <KpiCard label="Insights" value={`${quality?.segments?.length || 0} / ${quality?.anomalies?.length || 0} / ${quality?.tuning_suggestions?.length || 0}`} helper="Segments / anomalies / suggestions" />
          </Box>

          <SectionTitle>Segments</SectionTitle>
          <Table size="small" sx={{ mb: 3 }}>
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>Segment</TableCell>
                <TableCell>Matches</TableCell>
                <TableCell>Avg</TableCell>
                <TableCell>Low Rate</TableCell>
                <TableCell>Visit Rate</TableCell>
                <TableCell>Favorite Rate</TableCell>
                <TableCell>Apply Rate</TableCell>
                <TableCell>Apply Delta</TableCell>
                <TableCell>Sample</TableCell>
                <TableCell>Risk</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(quality?.segments || []).map(item => (
                <TableRow key={`${item.segment_type}:${item.segment_key}`} hover>
                  <TableCell>{item.segment_type}</TableCell>
                  <TableCell>{item.segment_label}</TableCell>
                  <TableCell>{item.match_count}</TableCell>
                  <TableCell>{metricValue(item.avg_score)}</TableCell>
                  <TableCell>{formatRate(item.low_score_rate)}</TableCell>
                  <TableCell>{formatRate(item.visit_rate)}</TableCell>
                  <TableCell>{formatRate(item.favorite_rate)}</TableCell>
                  <TableCell>{formatRate(item.application_rate)}</TableCell>
                  <TableCell>{Number(item.application_rate_delta || 0).toFixed(2)}pp</TableCell>
                  <TableCell><Chip label={item.sample_status} color={chipColor(item.sample_status)} size="small" /></TableCell>
                  <TableCell><Chip label={item.risk_level} color={chipColor(item.risk_level)} size="small" /></TableCell>
                </TableRow>
              ))}
              {(quality?.segments || []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={11}>No quality segment data.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>

          <SectionTitle>Experiment Confidence</SectionTitle>
          <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2 }}>
            {confidence ? (
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 2 }}>
                <KpiCard label="Control / Treatment" value={`${confidence.control_match_count} / ${confidence.treatment_match_count}`} helper={confidence.sample_status} />
                <KpiCard label="Apply Rate Delta" value={`${Number(confidence.application_rate_delta || 0).toFixed(2)}pp`} helper={`${formatRate(confidence.control_application_rate)} -> ${formatRate(confidence.treatment_application_rate)}`} />
                <KpiCard label="Avg Score Delta" value={metricValue(confidence.avg_score_delta)} />
                <Box>
                  <Chip label={confidence.confidence_status} color={chipColor(confidence.confidence_status)} sx={{ mb: 1 }} />
                  <Typography variant="body2" color="text.secondary">{confidence.decision_hint}</Typography>
                </Box>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">Select an Experiment ID to show confidence status.</Typography>
            )}
          </Paper>

          <SectionTitle>Anomalies</SectionTitle>
          <Table size="small" sx={{ mb: 3 }}>
            <TableHead>
              <TableRow>
                <TableCell>Severity</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Segment</TableCell>
                <TableCell>Evidence</TableCell>
                <TableCell>Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(quality?.anomalies || []).map((item, index) => (
                <TableRow key={`${item.type}:${item.segment_key}:${index}`} hover>
                  <TableCell><Chip label={item.severity} color={chipColor(item.severity)} size="small" /></TableCell>
                  <TableCell>{item.type}</TableCell>
                  <TableCell>{item.segment_label}</TableCell>
                  <TableCell>{item.evidence}</TableCell>
                  <TableCell>{item.suggested_next_action}</TableCell>
                </TableRow>
              ))}
              {(quality?.anomalies || []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={5}>No quality anomalies.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>

          <SectionTitle>Tuning Suggestions</SectionTitle>
          <Table size="small" sx={{ mb: 3 }}>
            <TableHead>
              <TableRow>
                <TableCell>Priority</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Dimension</TableCell>
                <TableCell>Segment</TableCell>
                <TableCell>Evidence</TableCell>
                <TableCell>Proposed Action</TableCell>
                <TableCell>Guardrail</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(quality?.tuning_suggestions || []).map((item, index) => (
                <TableRow key={`${item.suggestion_type}:${item.affected_segment}:${index}`} hover>
                  <TableCell><Chip label={item.priority} color={chipColor(item.priority)} size="small" /></TableCell>
                  <TableCell>{item.suggestion_type}</TableCell>
                  <TableCell>{item.dimension_key}</TableCell>
                  <TableCell>{item.affected_segment}</TableCell>
                  <TableCell>{item.evidence}</TableCell>
                  <TableCell>{item.proposed_action}</TableCell>
                  <TableCell>{item.guardrail}</TableCell>
                </TableRow>
              ))}
              {(quality?.tuning_suggestions || []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={7}>No tuning suggestions.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>

          <SectionTitle>Rule Versions</SectionTitle>
          <Table size="small" sx={{ mb: 3 }}>
            <TableHead>
              <TableRow>
                <TableCell>Rule</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Matches</TableCell>
                <TableCell>Avg</TableCell>
                <TableCell>High</TableCell>
                <TableCell>Medium</TableCell>
                <TableCell>Low</TableCell>
                <TableCell>Low Rate</TableCell>
                <TableCell>Visits</TableCell>
                <TableCell>Favorites</TableCell>
                <TableCell>Applications</TableCell>
                <TableCell>Apply Rate</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(quality?.rule_versions || []).map(item => (
                <TableRow key={item.rule_config_id || 'none'} hover>
                  <TableCell>{item.rule_config_name ? `${item.rule_config_name} V${item.rule_config_version}` : item.rule_config_id || '-'}</TableCell>
                  <TableCell><Chip label={item.rule_config_status || '-'} size="small" /></TableCell>
                  <MetricCells item={item} />
                </TableRow>
              ))}
              {(quality?.rule_versions || []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={12}>No quality data.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>

          <SectionTitle>Experiment Buckets</SectionTitle>
          <Table size="small" sx={{ mb: 3 }}>
            <TableHead>
              <TableRow>
                <TableCell>Bucket</TableCell>
                <TableCell>Matches</TableCell>
                <TableCell>Avg</TableCell>
                <TableCell>High</TableCell>
                <TableCell>Medium</TableCell>
                <TableCell>Low</TableCell>
                <TableCell>Low Rate</TableCell>
                <TableCell>Visits</TableCell>
                <TableCell>Favorites</TableCell>
                <TableCell>Applications</TableCell>
                <TableCell>Apply Rate</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {['control', 'treatment'].map(bucket => (
                <TableRow key={bucket} hover>
                  <TableCell><Chip label={bucket} size="small" /></TableCell>
                  <MetricCells item={buckets[bucket] || {}} />
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <SectionTitle>Daily Trend</SectionTitle>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Matches</TableCell>
                <TableCell>Avg</TableCell>
                <TableCell>High</TableCell>
                <TableCell>Medium</TableCell>
                <TableCell>Low</TableCell>
                <TableCell>Low Rate</TableCell>
                <TableCell>Visits</TableCell>
                <TableCell>Favorites</TableCell>
                <TableCell>Applications</TableCell>
                <TableCell>Apply Rate</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(quality?.time_buckets || []).map(item => (
                <TableRow key={item.date} hover>
                  <TableCell>{item.date}</TableCell>
                  <MetricCells item={item} />
                </TableRow>
              ))}
              {(quality?.time_buckets || []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={11}>No daily data.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </>
      )}
    </Box>
  )
}
