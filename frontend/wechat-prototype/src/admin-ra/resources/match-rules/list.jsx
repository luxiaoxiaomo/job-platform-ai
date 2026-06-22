import React from 'react'
import {
  Datagrid,
  FunctionField,
  List,
  SelectInput,
  TextField,
  useRecordContext,
} from 'react-admin'

const STATUS_LABELS = {
  active: 'Active',
  draft: 'Draft',
  testing: 'Testing',
  archived: 'Archived',
}

const STATUS_COLORS = {
  active: '#07C160',
  draft: '#999',
  testing: '#1187D6',
  archived: '#FA9D3B',
}

const StatusField = () => {
  const record = useRecordContext()
  if (!record) return null
  return (
    <span style={{ color: STATUS_COLORS[record.status] || '#999', fontSize: 13 }}>
      {STATUS_LABELS[record.status] || record.status}
    </span>
  )
}

const MatchRuleFilters = [
  <SelectInput
    key="scope"
    source="scope"
    label="Scope"
    choices={[
      { id: 'global', name: 'Global' },
      { id: 'job_category:tech', name: 'Tech category' },
    ]}
    alwaysOn
  />,
  <SelectInput
    key="template_key"
    source="template_key"
    label="Template"
    choices={[
      { id: 'default', name: 'Default' },
      { id: 'tech_jobs', name: 'Tech jobs' },
    ]}
  />,
]

export default function MatchRuleList() {
  return (
    <List filters={MatchRuleFilters} sort={{ field: 'updated_at', order: 'DESC' }}>
      <Datagrid rowClick="show" bulkActionButtons={false}>
        <TextField source="name" label="Rule" />
        <TextField source="template_name" label="Template" />
        <TextField source="template_key" label="Template Key" />
        <TextField source="scope" label="Scope" />
        <StatusField label="Status" />
        <FunctionField label="Version" render={(record) => `V${record.version ?? '-'}`} />
        <FunctionField label="Dimensions" render={(record) => `${record.dimensions?.length ?? 0}`} />
        <FunctionField
          label="Updated"
          render={(record) => (record.updated_at ? new Date(record.updated_at).toLocaleString('zh-CN') : '-')}
        />
      </Datagrid>
    </List>
  )
}
