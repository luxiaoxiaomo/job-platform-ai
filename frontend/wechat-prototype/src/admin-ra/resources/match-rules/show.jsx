import React, { useState } from 'react'
import {
  ArrayField,
  Button as RaButton,
  Datagrid,
  EditButton,
  FunctionField,
  Show,
  SimpleShowLayout,
  TextField,
  TopToolbar,
  useRecordContext,
} from 'react-admin'
import { Box, Chip, Collapse, Typography } from '@mui/material'
import HistoryIcon from '@mui/icons-material/History'
import PublishedWithChangesIcon from '@mui/icons-material/PublishedWithChanges'
import ScienceIcon from '@mui/icons-material/Science'
import { useNavigate } from 'react-router-dom'

const STATUS_META = {
  active: { label: 'Active', color: '#07C160' },
  draft: { label: 'Draft', color: '#999' },
  testing: { label: 'Testing', color: '#1187D6' },
  archived: { label: 'Archived', color: '#FA9D3B' },
}

const LogicField = () => {
  const record = useRecordContext()
  const [open, setOpen] = useState(false)
  if (!record?.logic || Object.keys(record.logic).length === 0) {
    return <span style={{ color: '#bbb' }}>-</span>
  }
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen(value => !value)}
        style={{ cursor: 'pointer', color: '#1187D6', fontSize: 12, border: 0, background: 'transparent', padding: 0 }}
      >
        {open ? 'Hide JSON' : 'Show JSON'}
      </button>
      <Collapse in={open}>
        <pre style={{ marginTop: 6, padding: 8, background: '#F7F8FA', borderRadius: 4, fontSize: 11, overflow: 'auto' }}>
          {JSON.stringify(record.logic, null, 2)}
        </pre>
      </Collapse>
    </div>
  )
}

const ShowActions = () => {
  const record = useRecordContext()
  const navigate = useNavigate()
  return (
    <TopToolbar>
      <EditButton />
      {record && (
        <RaButton
          label="History"
          onClick={() => navigate(`/admin-ra/match-rules/${record.id}/history`)}
        >
          <HistoryIcon />
        </RaButton>
      )}
      {record && (
        <RaButton
          label="Release"
          onClick={() => navigate(`/admin-ra/match-rules/${record.id}/release`)}
        >
          <PublishedWithChangesIcon />
        </RaButton>
      )}
      <RaButton
        label="AB Tests"
        onClick={() => navigate('/admin-ra/rule-experiments')}
      >
        <ScienceIcon />
      </RaButton>
    </TopToolbar>
  )
}

export default function MatchRuleShow() {
  return (
    <Show actions={<ShowActions />}>
      <SimpleShowLayout>
        <FunctionField
          label="Rule"
          render={(record) => <Typography variant="h6">{record.name}</Typography>}
        />
        <TextField source="template_name" label="Template" />
        <TextField source="template_key" label="Template Key" />
        <TextField source="strategy" label="Strategy" />
        <TextField source="scope" label="Scope" />
        <FunctionField
          label="Status"
          render={(record) => {
            const meta = STATUS_META[record.status] || { label: record.status, color: '#999' }
            return <Chip label={meta.label} size="small" sx={{ color: meta.color, borderColor: meta.color }} variant="outlined" />
          }}
        />
        <FunctionField label="Version" render={(record) => `V${record.version ?? '-'}`} />
        <FunctionField
          label="Updated"
          render={(record) => (record.updated_at ? new Date(record.updated_at).toLocaleString('zh-CN') : '-')}
        />
        <TextField source="description" label="Description" />

        <FunctionField
          label="Weight Summary"
          render={(record) => (
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip label={`Configured ${record.configured_total_weight ?? '-'}`} size="small" />
              <Chip label={`Effective ${record.effective_total_weight ?? '-'}`} size="small" color="primary" />
              <Chip label={`${record.dimensions?.filter(item => item.enabled).length ?? 0}/${record.dimensions?.length ?? 0} enabled`} size="small" />
            </Box>
          )}
        />

        <ArrayField source="dimensions">
          <Datagrid bulkActionButtons={false}>
            <TextField source="label" label="Dimension" />
            <TextField source="key" label="Key" />
            <FunctionField label="Enabled" render={(record) => (record.enabled ? 'Yes' : 'No')} />
            <FunctionField label="Configured Weight" render={(record) => `${record.configured_weight ?? record.weight ?? 0}%`} />
            <FunctionField label="Effective Weight" render={(record) => `${record.effective_weight ?? 0}%`} />
            <FunctionField label="Scoring" render={(record) => <span style={{ fontSize: 12, color: '#666' }}>{record.scoring_method || '-'}</span>} />
            <LogicField label="Logic" />
          </Datagrid>
        </ArrayField>
      </SimpleShowLayout>
    </Show>
  )
}
