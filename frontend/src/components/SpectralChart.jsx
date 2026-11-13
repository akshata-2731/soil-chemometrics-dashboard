import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { WAVELENGTH_ORDER } from '../utils/fileParser';

export default function SpectralChart({ sampleData, colors, title = "Sample Spectral Input" }) {
  if (!sampleData) {
    return (
      <div style={{ background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 12, padding: 24, textAlign: 'center', color: colors.textMuted }}>
        No sample selected for spectral graph.
      </div>
    );
  }

  const chartData = WAVELENGTH_ORDER.map(w => {
    const val = sampleData[`nm_${w}`] ?? sampleData[String(w)] ?? sampleData[w] ?? 0;
    return {
      wavelength: String(w),
      value: typeof val === 'number' ? parseFloat(val.toFixed(3)) : (parseFloat(val) || 0)
    };
  });

  return (
    <div style={{ background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 12, padding: 20, marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <h4 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: colors.textPrimary }}>{title}</h4>
        <span style={{ fontSize: 12, color: colors.accent, fontWeight: 600, background: colors.navLinkActiveBg, padding: '4px 10px', borderRadius: 6 }}>
          Sample: {sampleData.Sample_ID}
        </span>
      </div>

      <div style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
            <XAxis 
              dataKey="wavelength" 
              stroke={colors.textMuted} 
              tick={{ fill: colors.textMuted, fontSize: 11 }}
              label={{ value: 'Wavelength (nm)', position: 'insideBottom', offset: -15, fill: colors.textMuted, fontSize: 12, fontWeight: 600 }}
            />
            <YAxis 
              stroke={colors.textMuted} 
              tick={{ fill: colors.textMuted, fontSize: 11 }}
              label={{ value: 'Spectral Value', angle: -90, position: 'insideLeft', fill: colors.textMuted, fontSize: 12, fontWeight: 600 }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: colors.cardBg, 
                borderColor: colors.cardBorder, 
                color: colors.textPrimary,
                borderRadius: 8,
                boxShadow: colors.cardShadow,
                fontSize: 12
              }}
              formatter={(val) => [`${val}`, 'Spectral Value']}
              labelFormatter={(label) => `Wavelength: ${label} nm`}
            />
            <Line 
              type="linear" 
              dataKey="value" 
              stroke={colors.spectralLine} 
              strokeWidth={2.5}
              dot={{ r: 4, fill: colors.spectralDot, strokeWidth: 1 }}
              activeDot={{ r: 7 }}
              name="Spectral Value"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
