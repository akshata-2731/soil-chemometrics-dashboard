import re
import os

FILE = 'frontend/src/pages/ModeBatch.jsx'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

new_metrics_ui = """              {/* METRICS SUMMARY */}
              {(() => {
                const ov = calculateMetrics(result.results);
                
                const allMetrics = selectedNutrients.map(nut => {
                    const data = result.results.filter(r => r.nutrient === nut);
                    return { nut, ...calculateMetrics(data) };
                });

                return (
                  <div style={{ marginBottom: 24 }}>
                    <div style={{ background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: 16 }}>
                      <h4 style={{ fontSize: 14, fontWeight: 700, color: colors.textPrimary, margin: '0 0 16px 0' }}>Performance Metrics By Nutrient</h4>
                      
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
                        {allMetrics.map(m => (
                          <div key={m.nut} style={{ background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 6, padding: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                            <div style={{ fontWeight: 800, color: colors.accent, fontSize: 14, borderBottom: `1px solid ${colors.tableBorder}`, paddingBottom: 4 }}>{m.nut}</div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                              <span style={{ color: colors.textMuted }}>R²:</span>
                              <span style={{ fontWeight: 600, color: colors.textPrimary }}>{m.r2}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                              <span style={{ color: colors.textMuted }}>Accuracy:</span>
                              <span style={{ fontWeight: 600, color: '#10b981' }}>{m.accuracy}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                              <span style={{ color: colors.textMuted }}>RMSE (Error):</span>
                              <span style={{ fontWeight: 600, color: colors.textSecondary }}>{m.rmse}</span>
                            </div>
                          </div>
                        ))}
                        
                        {/* Overall Card */}
                        <div style={{ background: 'rgba(56, 189, 248, 0.05)', border: `1px dashed ${colors.accent}`, borderRadius: 6, padding: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                          <div style={{ fontWeight: 800, color: colors.textPrimary, fontSize: 14, borderBottom: `1px solid ${colors.tableBorder}`, paddingBottom: 4 }}>GLOBAL AVERAGE</div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                            <span style={{ color: colors.textMuted }}>Avg R²:</span>
                            <span style={{ fontWeight: 600, color: colors.textPrimary }}>{ov.r2}</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                            <span style={{ color: colors.textMuted }}>Avg Accuracy:</span>
                            <span style={{ fontWeight: 600, color: '#10b981' }}>{ov.accuracy}</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                            <span style={{ color: colors.textMuted }}>Global RMSE:</span>
                            <span style={{ fontWeight: 600, color: colors.textSecondary }}>{ov.rmse}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Results Table */}\n"""

# Regex to find the existing metrics block and replace it
pattern = r"\{/\* METRICS SUMMARY \*/\}.*?\{/\* Results Table \*/\}"
content = re.sub(pattern, new_metrics_ui.strip(), content, flags=re.DOTALL)

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated metrics UI to show all nutrients side-by-side.")
