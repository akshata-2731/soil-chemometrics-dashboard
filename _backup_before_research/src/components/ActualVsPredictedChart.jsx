import React from 'react';
import { ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';

export default function ActualVsPredictedChart({ 
  results, 
  selectedNutrient, 
  colors, 
  title = "Actual vs Predicted",
  isSingleSample = false 
}) {
  const nutrientResults = (results || []).filter(r => r.nutrient === selectedNutrient);

  const hasActual = nutrientResults.some(
    r => r.actual !== null && r.actual !== undefined && r.actual !== '' && !isNaN(parseFloat(r.actual))
  );

  const chartData = nutrientResults.map(r => {
    const act = (r.actual !== null && r.actual !== undefined && r.actual !== '' && !isNaN(parseFloat(r.actual))) 
      ? parseFloat(parseFloat(r.actual).toFixed(3)) 
      : null;
    const pred = (r.final_prediction !== null && r.final_prediction !== undefined && !isNaN(parseFloat(r.final_prediction)))
      ? parseFloat(parseFloat(r.final_prediction).toFixed(3))
      : null;

    return {
      sample: r.sample_id,
      Predicted: pred,
      Actual: act
    };
  });

  return (
    <div style={{ background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 12, padding: 20, marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <h4 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: colors.textPrimary }}>{title}</h4>
        <span style={{ fontSize: 12, color: colors.accent, fontWeight: 600, background: colors.navLinkActiveBg, padding: '4px 10px', borderRadius: 6 }}>
          Nutrient: {selectedNutrient}
        </span>
      </div>

      {!hasActual && (
        <div style={{ 
          background: colors.name === 'dark' ? '#1e293b' : '#f1f5f9', 
          color: colors.textMuted, 
          borderRadius: 8, 
          padding: '8px 14px', 
          fontSize: 12, 
          marginBottom: 14,
          border: `1px dashed ${colors.cardBorder}`
        }}>
          ⓘ Actual values not available for this dataset. Displaying predicted values only.
        </div>
      )}

      {chartData.length === 0 ? (
        <div style={{ padding: 24, textAlign: 'center', color: colors.textMuted, fontSize: 13 }}>
          No prediction data available for {selectedNutrient}.
        </div>
      ) : (
        <div style={{ width: '100%', height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
              <XAxis 
                dataKey="sample" 
                stroke={colors.textMuted} 
                tick={{ fill: colors.textMuted, fontSize: 11 }}
                label={{ value: 'Sample', position: 'insideBottom', offset: -15, fill: colors.textMuted, fontSize: 12, fontWeight: 600 }}
              />
              <YAxis 
                stroke={colors.textMuted} 
                tick={{ fill: colors.textMuted, fontSize: 11 }}
                label={{ value: `${selectedNutrient} Value`, angle: -90, position: 'insideLeft', fill: colors.textMuted, fontSize: 12, fontWeight: 600 }}
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
              />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ color: colors.textPrimary, fontSize: 12 }} />
              {hasActual && (
                <Line 
                  type="linear" 
                  dataKey="Actual" 
                  stroke={colors.actualSeries} 
                  strokeWidth={2.5}
                  dot={{ r: 4 }}
                  activeDot={{ r: 7 }}
                  connectNulls={true}
                  isAnimationActive={false}
                />
              )}
              <Line 
                type="linear" 
                dataKey="Predicted" 
                stroke={colors.predictedSeries} 
                strokeWidth={2.5}
                dot={{ r: 4 }}
                activeDot={{ r: 7 }}
                connectNulls={true}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
