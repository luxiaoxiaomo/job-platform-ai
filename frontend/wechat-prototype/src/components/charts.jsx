import React from 'react'

/* ============ 雷达图（轻量 SVG，无依赖） ============
   data: [{ key, score }]  score 0-100
*/
export function RadarChart({ data, size = 220, color = '#07C160' }) {
  const cx = size / 2, cy = size / 2
  const R = size / 2 - 42  // 从 34 改为 42，给标签更多空间
  const n = data.length
  const levels = [0.25, 0.5, 0.75, 1]

  const pt = (i, r) => {
    const ang = (Math.PI * 2 * i) / n - Math.PI / 2
    return [cx + r * Math.cos(ang), cy + r * Math.sin(ang)]
  }
  const gridPoly = (ratio) => data.map((_, i) => pt(i, R * ratio).join(',')).join(' ')
  const dataPoly = data.map((d, i) => pt(i, R * (d.score / 100)).join(',')).join(' ')

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* 网格 */}
      {levels.map((lv, i) => (
        <polygon key={i} points={gridPoly(lv)} fill="none" stroke="#E5E5E5" strokeWidth="1" />
      ))}
      {/* 轴线 */}
      {data.map((_, i) => {
        const [x, y] = pt(i, R)
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#EDEDED" strokeWidth="1" />
      })}
      {/* 数据多边形 */}
      <polygon points={dataPoly} fill={color} fillOpacity="0.18" stroke={color} strokeWidth="2" />
      {data.map((d, i) => {
        const [x, y] = pt(i, R * (d.score / 100))
        return <circle key={i} cx={x} cy={y} r="2.5" fill={color} />
      })}
      {/* 标签 */}
      {data.map((d, i) => {
        const [x, y] = pt(i, R + 22)
        const label = d.key
        // 四字或更长的标签换行显示
        if (label.length >= 4) {
          return (
            <g key={i}>
              <text x={x} y={y - 6} fontSize="11" fill="#666"
                textAnchor={Math.abs(x - cx) < 6 ? 'middle' : x > cx ? 'start' : 'end'}
                dominantBaseline="middle">
                {label.slice(0, 2)}
              </text>
              <text x={x} y={y + 6} fontSize="11" fill="#666"
                textAnchor={Math.abs(x - cx) < 6 ? 'middle' : x > cx ? 'start' : 'end'}
                dominantBaseline="middle">
                {label.slice(2)}
              </text>
            </g>
          )
        }
        return (
          <text key={i} x={x} y={y} fontSize="11" fill="#666"
            textAnchor={Math.abs(x - cx) < 6 ? 'middle' : x > cx ? 'start' : 'end'}
            dominantBaseline="middle">
            {label}
          </text>
        )
      })}
    </svg>
  )
}

/* ============ 折线趋势图（轻量 SVG） ============ */
export function LineChart({ series, labels, width = 320, height = 140, color = '#07C160' }) {
  const pad = 24, w = width - pad * 2, h = height - pad * 2
  const max = Math.max(...series) * 1.1 || 1
  const stepX = w / (series.length - 1)
  const points = series.map((v, i) => [pad + i * stepX, pad + h - (v / max) * h])
  const path = points.map((p, i) => (i === 0 ? 'M' : 'L') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ')
  const area = path + ` L${pad + w} ${pad + h} L${pad} ${pad + h} Z`
  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`}>
      {[0.5, 1].map((r, i) => (
        <line key={i} x1={pad} y1={pad + h * (1 - r)} x2={pad + w} y2={pad + h * (1 - r)} stroke="#F0F0F0" strokeWidth="1" />
      ))}
      <path d={area} fill={color} fillOpacity="0.1" />
      <path d={path} fill="none" stroke={color} strokeWidth="2" />
      {points.map((p, i) => <circle key={i} cx={p[0]} cy={p[1]} r="2.5" fill={color} />)}
      {labels && labels.map((l, i) => (
        <text key={i} x={pad + i * stepX} y={height - 4} fontSize="9" fill="#aaa" textAnchor="middle">{l}</text>
      ))}
    </svg>
  )
}

/* ============ 柱状对比条（用于候选人对比 / 分项得分） ============ */
export function ScoreBar({ label, score, color = '#07C160', max = 100 }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div className="row between tiny" style={{ marginBottom: 4 }}>
        <span className="muted">{label}</span>
        <span style={{ color, fontWeight: 600 }}>{score}{max === 100 ? '' : ''}</span>
      </div>
      <div className="progress"><div className="bar" style={{ width: (score / max * 100) + '%', background: color }} /></div>
    </div>
  )
}
