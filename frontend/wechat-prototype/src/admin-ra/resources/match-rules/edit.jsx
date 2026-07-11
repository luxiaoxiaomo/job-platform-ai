import React, { useEffect, useMemo, useState } from 'react'
import {
  ArrayInput,
  BooleanInput,
  Edit,
  NumberInput,
  SelectInput,
  SimpleForm,
  SimpleFormIterator,
  TextInput,
  useNotify,
  useRedirect,
} from 'react-admin'
import { useFormContext, useWatch } from 'react-hook-form'
import { Box, Typography } from '@mui/material'

const STATUS_CHOICES = [
  { id: 'draft', name: 'Draft' },
  { id: 'active', name: 'Active' },
  { id: 'testing', name: 'Testing' },
  { id: 'archived', name: 'Archived' },
]

const EnabledWeightTotal = () => {
  const dimensions = useWatch({ name: 'dimensions' })
  const total = useMemo(() => {
    if (!Array.isArray(dimensions)) return 0
    return Number(
      dimensions
        .filter(item => item?.enabled)
        .reduce((sum, item) => sum + Number(item?.weight ?? item?.configured_weight ?? 0), 0)
        .toFixed(2)
    )
  }, [dimensions])

  return (
    <Box sx={{ padding: 1, background: '#F7F8FA', borderRadius: 1, mb: 2 }}>
      <Typography variant="body2" color={total > 0 ? 'primary' : 'error'}>
        Enabled configured weight total: <strong>{total}</strong>
        {total <= 0 ? ' (must be greater than 0)' : ''}
      </Typography>
    </Box>
  )
}

const LogicJsonInput = ({ source }) => {
  const { setValue, watch } = useFormContext()
  const value = watch(source)
  const [text, setText] = useState(() => JSON.stringify(value || {}, null, 2))
  const [error, setError] = useState('')

  useEffect(() => {
    setText(JSON.stringify(value || {}, null, 2))
    setError('')
  }, [value])

  const handleChange = (event) => {
    const nextText = event.target.value
    setText(nextText)
    try {
      const parsed = JSON.parse(nextText || '{}')
      setError('')
      setValue(source, parsed, { shouldDirty: true, shouldValidate: true })
    } catch {
      setError('Invalid JSON')
    }
  }

  return (
    <Box sx={{ width: '100%' }}>
      <textarea
        value={text}
        onChange={handleChange}
        rows={5}
        style={{
          width: '100%',
          fontFamily: 'monospace',
          fontSize: 12,
          padding: 8,
          borderRadius: 4,
          border: error ? '1px solid #FA5151' : '1px solid #ccc',
        }}
      />
      {error ? <Typography variant="caption" color="error">{error}</Typography> : null}
    </Box>
  )
}

const DimensionsInput = () => (
  <ArrayInput source="dimensions" label="Dimensions">
    <SimpleFormIterator disableReordering inline>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center', width: '100%' }}>
        <TextInput source="label" label="Label" />
        <TextInput source="key" label="Key" InputProps={{ readOnly: true }} />
        <NumberInput source="weight" label="Weight" min={0} max={100} step={1} />
        <BooleanInput source="enabled" label="Enabled" />
        <NumberInput source="sort_order" label="Sort" step={1} />
      </Box>
      <TextInput source="description" label="Description" fullWidth />
      <TextInput source="scoring_method" label="Scoring Method" fullWidth />
      <Typography variant="caption" color="textSecondary">Logic JSON</Typography>
      <LogicJsonInput source="logic" />
    </SimpleFormIterator>
  </ArrayInput>
)

export default function MatchRuleEdit() {
  const notify = useNotify()
  const redirect = useRedirect()

  const validate = (values) => {
    const errors = {}
    if (!values.name?.trim()) {
      errors.name = 'Rule name is required'
    }
    const dimensions = values.dimensions || []
    if (!dimensions.some(item => item.enabled && Number(item.weight ?? item.configured_weight ?? 0) > 0)) {
      errors.dimensions = 'At least one enabled dimension must have a positive weight'
    }
    return errors
  }

  return (
    <Edit
      title="Edit Match Rule"
      mutationMode="pessimistic"
      redirect={false}
      mutationOptions={{
        onSuccess: (data) => {
          const created = data?.data || data
          notify('New rule version created', { type: 'success' })
          redirect('show', 'match-rules', created?.id)
        },
        onError: (error) => {
          notify(error?.message || 'Save failed', { type: 'error' })
        },
      }}
    >
      <SimpleForm validate={validate}>
        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
          Saving creates a new version. The current version is not overwritten.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', width: '100%' }}>
          <TextInput source="name" label="Rule Name" />
          <SelectInput source="status" label="Status" choices={STATUS_CHOICES} />
          <TextInput source="scope" label="Scope" defaultValue="global" />
          <TextInput source="template_name" label="Template" InputProps={{ readOnly: true }} />
          <TextInput source="template_key" label="Template Key" InputProps={{ readOnly: true }} />
        </Box>
        <TextInput source="description" label="Description" fullWidth multiline />
        <EnabledWeightTotal />
        <DimensionsInput />
      </SimpleForm>
    </Edit>
  )
}
