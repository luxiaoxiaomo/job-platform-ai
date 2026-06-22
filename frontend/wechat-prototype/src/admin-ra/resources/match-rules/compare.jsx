import React, { useEffect, useState } from 'react'
import { Title, useDataProvider, useNotify } from 'react-admin'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'

const CHANGE_COLOR = {
  added: 'success',
  removed: 'error',
  changed: 'warning',
  unchanged: 'default',
}

export default function MatchRuleCompare() {
  const { id, targetId } = useParams()
  const navigate = useNavigate()
  const dataProvider = useDataProvider()
  const notify = useNotify()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    dataProvider
      .compareRuleConfigs(id, targetId)
      .then((result) => {
        if (alive) setData(result)
      })
      .catch((err) => {
        notify(err?.message || 'Compare failed', { type: 'error' })
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [dataProvider, id, notify, targetId])

  return (
    <Box sx={{ p: 3 }}>
      <Title title="Rule Version Compare" />
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(`/admin-ra/match-rules/${id}/history`)}>
        Back to history
      </Button>

      {loading && <Box sx={{ mt: 3 }}><CircularProgress size={24} /></Box>}
      {!loading && data && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            V{data.base.version} vs V{data.target.version}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            <Chip label={`Changed ${data.summary.changed}`} color="warning" size="small" />
            <Chip label={`Added ${data.summary.added}`} color="success" size="small" />
            <Chip label={`Removed ${data.summary.removed}`} color="error" size="small" />
            <Chip label={`Unchanged ${data.summary.unchanged}`} size="small" />
          </Box>

          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Dimension</TableCell>
                <TableCell>Change</TableCell>
                <TableCell>Base Weight</TableCell>
                <TableCell>Target Weight</TableCell>
                <TableCell>Delta</TableCell>
                <TableCell>Enabled Changed</TableCell>
                <TableCell>Logic Changed</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.dimensions.map((item) => (
                <TableRow key={item.key} hover>
                  <TableCell>{item.label} ({item.key})</TableCell>
                  <TableCell>
                    <Chip label={item.change_type} color={CHANGE_COLOR[item.change_type] || 'default'} size="small" />
                  </TableCell>
                  <TableCell>{item.base_weight ?? '-'}</TableCell>
                  <TableCell>{item.target_weight ?? '-'}</TableCell>
                  <TableCell>{item.weight_delta ?? '-'}</TableCell>
                  <TableCell>{item.enabled_changed ? 'Yes' : 'No'}</TableCell>
                  <TableCell>{item.logic_changed ? 'Yes' : 'No'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      )}
    </Box>
  )
}
