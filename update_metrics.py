import re
import os

FILE = 'frontend/src/pages/ModeBatch.jsx'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

calc_metrics = """
  const calculateMetrics = (resultsList) => {
    if (!resultsList) return { r2: 'N/A', rmse: 'N/A', accuracy: 'N/A', n: 0 };
    const valid = resultsList.filter(r => r.actual != null && r.final_prediction != null);
    if (valid.length < 2) return { r2: 'N/A', rmse: 'N/A', accuracy: 'N/A', n: valid.length };

    const actuals = valid.map(r => r.actual);
    const preds = valid.map(r => r.final_prediction);
    const meanActual = actuals.reduce((a, b) => a + b, 0) / valid.length;

    let ssTot = 0;
    let ssRes = 0;
    let sumSqErr = 0;
    let mapeSum = 0;

    for (let i = 0; i < valid.length; i++) {
      const a = actuals[i];
      const p = preds[i];
      ssTot += Math.pow(a - meanActual, 2);
      ssRes += Math.pow(a - p, 2);
      sumSqErr += Math.pow(a - p, 2);
      if (a !== 0) {
        mapeSum += Math.abs((a - p) / a);
      } else {
        mapeSum += Math.abs(a - p) > 0 ? 1 : 0;
      }
    }

    const r2 = ssTot > 0 ? 1 - (ssRes / ssTot) : 0;
    const rmse = Math.sqrt(sumSqErr / valid.length);
    const accuracy = Math.max(0, 100 - ((mapeSum / valid.length) * 100));

    return { 
      r2: r2.toFixed(3), 
      rmse: rmse.toFixed(3), 
      accuracy: accuracy.toFixed(1) + '%',
      n: valid.length
    };
  };

"""

# Insert function before `const exportCSV`
content = content.replace("const exportCSV = () => {", calc_metrics + "  const exportCSV = () => {")

metrics_ui = """
              {/* METRICS SUMMARY */}
              {(() => {
                const ov = calculateMetrics(result.results);
                const nu = calculateMetrics(result.results.filter(r => r.nutrient === resultNutrient));
                return (
                  <div style={{ marginBottom: 24, display: 'flex', gap: 20 }}>
                    {/* Overall */}
                    <div style={{ flex: 1, background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: 16 }}>
                      <h4 style={{ fontSize: 14, fontWeight: 700, color: colors.textPrimary, margin: '0 0 12px 0' }}>Overall Metrics (All Nutrients)</h4>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
                        <div><div style={{ fontSize: 11, color: colors.textMuted }}>Valid Samples</div><div style={{ fontSize: 14, fontWeight: 700, color: colors.textPrimary }}>{ov.n}</div></div>
                        <div><div style={{ fontSize: 11, color: colors.textMuted }}>Overall R²</div><div style={{ fontSize: 14, fontWeight: 700, color: colors.accent }}>{ov.r2}</div></div>
                        <div><div style={{ fontSize: 11, color: colors.textMuted }}>Accuracy</div><div style={{ fontSize: 14, fontWeight: 700, color: '#10b981' }}>{ov.accuracy}</div></div>
                        <div><div style={{ fontSize: 11, color: colors.textMuted }}>RMSE</div><div style={{ fontSize: 14, fontWeight: 700, color: colors.textSecondary }}>{ov.rmse}</div></div>
                      </div>
                    </div>
                    {/* Nutrient Specific */}
                    <div style={{ flex: 1, background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: 16 }}>
                      <h4 style={{ fontSize: 14, fontWeight: 700, color: colors.textPrimary, margin: '0 0 12px 0' }}>{resultNutrient} Metrics</h4>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
                        <div><div style={{ fontSize: 11, color: colors.textMuted }}>Valid Samples</div><div style={{ fontSize: 14, fontWeight: 700, color: colors.textPrimary }}>{nu.n}</div></div>
                        <div><div style={{ fontSize: 11, color: colors.textMuted }}>{resultNutrient} R²</div><div style={{ fontSize: 14, fontWeight: 700, color: colors.accent }}>{nu.r2}</div></div>
                        <div><div style={{ fontSize: 11, color: colors.textMuted }}>Accuracy</div><div style={{ fontSize: 14, fontWeight: 700, color: '#10b981' }}>{nu.accuracy}</div></div>
                        <div><div style={{ fontSize: 11, color: colors.textMuted }}>RMSE</div><div style={{ fontSize: 14, fontWeight: 700, color: colors.textSecondary }}>{nu.rmse}</div></div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Results Table */}
"""

content = content.replace("{/* Results Table */}", metrics_ui)

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated ModeBatch.jsx with Metrics UI")
