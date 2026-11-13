import React, { useState } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { WAVELENGTH_ORDER } from '../utils/fileParser';

// 21 distinct rainbow-style colors representing the 21 wavelengths
export const WAVELENGTH_RAINBOW_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16', 
  '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9', 
  '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', 
  '#ec4899', '#f43f5e', '#dc2626', '#c026d3', '#7c3aed', '#2563eb'
];

export default function BatchSpectralChart({ samples = [], colors, title = "Batch Spectral Input" }) {
  const [highlightSample, setHighlightSample] = useState(null);

  if (!samples || samples.length === 0) {
    return (
      <div style={{ background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 12, padding: 24, textAlign: 'center', color: colors.textMuted }}>
        No samples uploaded for batch spectral graph.
      </div>
    );
  }

  // Transform data: 21 items (one for each wavelength), containing values for ALL samples
  const chartData = WAVELENGTH_ORDER.map((w, wIdx) => {
    const row = {
      wavelength: String(w),
      wIndex: wIdx,
      wColor: WAVELENGTH_RAINBOW_COLORS[wIdx % WAVELENGTH_RAINBOW_COLORS.length]
    };
    samples.forEach(s => {
      const val = s[`nm_${w}`] ?? s[String(w)] ?? s[w] ?? 0;
      row[s.Sample_ID] = typeof val === 'number' ? parseFloat(val.toFixed(3)) : (parseFloat(val) || 0);
    });
    return row;
  });

  // Generate distinct line stroke colors for samples
  const getSampleStroke = (idx, total) => {
    // Generate evenly spaced hues across sample lines so all curves remain distinct
    const hue = (idx * 137.5) % 360; // Golden ratio hue distribution
    return colors.name === 'dark'
      ? `hsl(${hue}, 80%, 65%)`
      : `hsl(${hue}, 75%, 45%)`;
  };

  return (
    <div style={{ background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 12, padding: 20, marginBottom: 20, boxShadow: colors.cardShadow }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <h4 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: colors.accent }}>{title}</h4>
          <div style={{ fontSize: 12, color: colors.textMuted, marginTop: 2 }}>
            Plotting all {samples.length} sample spectral curves across 21 wavelengths
          </div>
        </div>
        <span style={{ fontSize: 13, color: colors.accent, fontWeight: 700, background: colors.navLinkActiveBg, padding: '6px 14px', borderRadius: 20, border: `1px solid ${colors.accent}40` }}>
          Samples: {samples.length}
        </span>
      </div>

      {/* Wavelength Rainbow Legend Bar */}
      <div style={{ marginBottom: 14, background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: '10px 12px' }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: colors.textMuted, marginBottom: 6 }}>
          WAVELENGTH COLOR KEY (21 Wavelengths):
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {WAVELENGTH_ORDER.map((w, idx) => {
            const wColor = WAVELENGTH_RAINBOW_COLORS[idx % WAVELENGTH_RAINBOW_COLORS.length];
            return (
              <span 
                key={w} 
                style={{ 
                  display: 'inline-flex', 
                  alignItems: 'center', 
                  gap: 4, 
                  fontSize: 11, 
                  fontWeight: 600, 
                  color: colors.textPrimary,
                  background: colors.cardBg,
                  padding: '2px 6px',
                  borderRadius: 4,
                  border: `1px solid ${colors.cardBorder}`
                }}
              >
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: wColor, display: 'inline-block' }} />
                {w}nm
              </span>
            );
          })}
        </div>
      </div>

      {/* Recharts Multi-Sample Line Chart */}
      <div style={{ width: '100%', height: 380 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 15, right: 25, left: 10, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
            <XAxis 
              dataKey="wavelength" 
              stroke={colors.textMuted} 
              tick={(props) => {
                const { x, y, payload, index } = props;
                const color = WAVELENGTH_RAINBOW_COLORS[index % WAVELENGTH_RAINBOW_COLORS.length];
                return (
                  <g transform={`translate(${x},${y})`}>
                    <text x={0} y={0} dy={14} textAnchor="middle" fill={color} fontSize={11} fontWeight={800}>
                      {payload.value}
                    </text>
                  </g>
                );
              }}
              label={{ value: 'Wavelength (nm)', position: 'insideBottom', offset: -15, fill: colors.textMuted, fontSize: 12, fontWeight: 700 }}
            />
            <YAxis 
              stroke={colors.textMuted} 
              tick={{ fill: colors.textMuted, fontSize: 11 }}
              label={{ value: 'Spectral Value', angle: -90, position: 'insideLeft', fill: colors.textMuted, fontSize: 12, fontWeight: 700 }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: colors.cardBg, 
                borderColor: colors.cardBorder, 
                color: colors.textPrimary,
                borderRadius: 8,
                boxShadow: colors.cardShadow,
                fontSize: 12,
                maxHeight: 250,
                overflowY: 'auto'
              }}
              formatter={(val, name) => [`${val}`, name]}
              labelFormatter={(label) => `Wavelength: ${label} nm`}
            />

            {/* Render a Line for EVERY sample in the batch */}
            {samples.map((s, idx) => {
              const strokeColor = getSampleStroke(idx, samples.length);
              const isHighlighted = highlightSample === s.Sample_ID;
              const opacity = highlightSample ? (isHighlighted ? 1.0 : 0.15) : 0.75;
              const strokeWidth = isHighlighted ? 3 : 1.5;

              return (
                <Line 
                  key={s.Sample_ID} 
                  type="linear" 
                  dataKey={s.Sample_ID} 
                  stroke={strokeColor} 
                  strokeWidth={strokeWidth}
                  strokeOpacity={opacity}
                  dot={(props) => {
                    const wColor = WAVELENGTH_RAINBOW_COLORS[props.index % WAVELENGTH_RAINBOW_COLORS.length];
                    return (
                      <circle 
                        key={`${s.Sample_ID}-${props.index}`} 
                        cx={props.cx} 
                        cy={props.cy} 
                        r={isHighlighted ? 4.5 : 3} 
                        fill={wColor} 
                        stroke={colors.cardBg} 
                        strokeWidth={0.5}
                        opacity={opacity} 
                      />
                    );
                  }}
                  activeDot={{ r: 6 }}
                  name={s.Sample_ID}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Optional Sample Highlight / Quick Filter Control */}
      {samples.length > 10 && (
        <details style={{ marginTop: 14 }}>
          <summary style={{ cursor: 'pointer', fontSize: 12, fontWeight: 600, color: colors.textMuted }}>
            Optional: Highlight specific sample curve on graph ({samples.length} curves total)
          </summary>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8, maxHeight: 100, overflowY: 'auto', padding: 6, background: colors.inputBg, borderRadius: 6 }}>
            <button
              onClick={() => setHighlightSample(null)}
              style={{
                fontSize: 11,
                padding: '2px 8px',
                borderRadius: 4,
                border: `1px solid ${colors.cardBorder}`,
                background: highlightSample === null ? colors.accent : colors.cardBg,
                color: highlightSample === null ? '#fff' : colors.textPrimary,
                cursor: 'pointer'
              }}
            >
              Show All {samples.length} Curves
            </button>
            {samples.map(s => (
              <button
                key={s.Sample_ID}
                onClick={() => setHighlightSample(highlightSample === s.Sample_ID ? null : s.Sample_ID)}
                style={{
                  fontSize: 11,
                  padding: '2px 8px',
                  borderRadius: 4,
                  border: `1px solid ${colors.cardBorder}`,
                  background: highlightSample === s.Sample_ID ? colors.accent : colors.cardBg,
                  color: highlightSample === s.Sample_ID ? '#fff' : colors.textPrimary,
                  cursor: 'pointer'
                }}
              >
                {s.Sample_ID}
              </button>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
