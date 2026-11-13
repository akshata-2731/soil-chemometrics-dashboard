import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTheme } from '../context/ThemeContext';
import { ALL_TARGETS } from '../utils/fileParser';
import ActualVsPredictedChart from '../components/ActualVsPredictedChart';

const BASE = 'http://127.0.0.1:5000';

const MODE_LABELS = { MODE_1_BATCH: 'Batch Analysis', MODE_2_SINGLE: 'Single Nutrient', MODE_3_ALL12: 'All 12 Nutrients' };
const STATUS_COLORS = { HIGH: '#16a34a', ADEQUATE: '#16a34a', LOW: '#dc2626', DEFICIENT: '#dc2626', MEDIUM: '#ca8a04' };

export default function History() {
  const { colors } = useTheme();
  const [runs, setRuns] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [runDetail, setRunDetail] = useState({});
  const [selectedNutrientMap, setSelectedNutrientMap] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${BASE}/api/runs`)
      .then(r => { setRuns(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const toggleRun = async (run_id) => {
    if (expanded === run_id) { 
      setExpanded(null); 
      return; 
    }
    setExpanded(run_id);
    if (!runDetail[run_id]) {
      try {
        const r = await axios.get(`${BASE}/api/runs/${run_id}`);
        setRunDetail(prev => ({ ...prev, [run_id]: r.data }));
        if (r.data.predictions && r.data.predictions.length > 0) {
          setSelectedNutrientMap(pm => ({ ...pm, [run_id]: r.data.predictions[0].nutrient }));
        }
      } catch (err) {
        console.error("Failed to load run detail:", err);
      }
    }
  };

  const setRunNutrient = (run_id, nut) => {
    setSelectedNutrientMap(prev => ({ ...prev, [run_id]: nut }));
  };

  const cardStyle = {
    background: colors.cardBg,
    border: `1px solid ${colors.cardBorder}`,
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    boxShadow: colors.cardShadow,
    transition: 'all 0.15s',
  };

  const inputStyle = {
    background: colors.inputBg,
    color: colors.inputColor,
    border: `1px solid ${colors.inputBorder}`,
    borderRadius: 6,
    padding: '6px 12px',
    fontSize: 13,
  };

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 800, color: colors.textPrimary, marginBottom: 20 }}>📋 Run Execution History</h2>

      {loading && <div style={{ color: colors.textMuted, padding: 20 }}>Loading history records...</div>}
      {!loading && !runs.length && (
        <div style={{ color: colors.textMuted, padding: 30, textAlign: 'center', background: colors.cardBg, borderRadius: 12, border: `1px solid ${colors.cardBorder}` }}>
          No execution runs recorded yet. Perform an analysis to view history.
        </div>
      )}

      {runs.map(run => {
        const ml = MODE_LABELS[run.mode] || run.mode;
        const isExpanded = expanded === run.run_id;
        const detail = runDetail[run.run_id];
        const activeNutrient = selectedNutrientMap[run.run_id] || 'OC';
        const availableNutrients = detail?.predictions ? Array.from(new Set(detail.predictions.map(p => p.nutrient))) : ALL_TARGETS;

        return (
          <div key={run.run_id} style={{ ...cardStyle, border: `1px solid ${isExpanded ? colors.accent : colors.cardBorder}` }}>
            <div 
              onClick={() => toggleRun(run.run_id)} 
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', flexWrap: 'wrap', gap: 10 }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ color: colors.accent, fontWeight: 800, fontSize: 15, fontFamily: 'monospace' }}>{run.run_id}</span>
                  <span style={{ background: colors.navLinkActiveBg, color: colors.navLinkActive, borderRadius: 6, padding: '2px 10px', fontSize: 12, fontWeight: 700 }}>
                    {ml}
                  </span>
                </div>
                <div style={{ color: colors.textMuted, fontSize: 12, marginTop: 6 }}>
                  Date: <strong>{run.date}</strong> ({run.time}) &nbsp;|&nbsp; Samples: <strong>{run.samples}</strong> &nbsp;|&nbsp; Nutrients: <strong>{run.nutrients}</strong>
                </div>
              </div>
              <span style={{ color: colors.textMuted, fontSize: 16, fontWeight: 700 }}>
                {isExpanded ? '▲ Collapse' : '▼ View Graphs & Details'}
              </span>
            </div>

            {isExpanded && detail && (
              <div style={{ marginTop: 20, borderTop: `1px solid ${colors.cardBorder}`, paddingTop: 20 }}>
                
                {/* RUN-SCOPED ACTUAL VS PREDICTED GRAPH */}
                <div style={{ marginBottom: 20 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                    <label style={{ fontSize: 13, fontWeight: 700, color: colors.textPrimary }}>Nutrient Selector for Run Graph:</label>
                    <select
                      style={inputStyle}
                      value={activeNutrient}
                      onChange={e => setRunNutrient(run.run_id, e.target.value)}
                    >
                      {availableNutrients.map(t => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </div>

                  <ActualVsPredictedChart 
                    results={detail.predictions.map(p => ({
                      ...p,
                      raw_prediction: p.raw_pred,
                      final_prediction: p.final_pred,
                      calibration_source: p.calib_source
                    }))} 
                    selectedNutrient={activeNutrient} 
                    colors={colors} 
                    title={`Actual vs Predicted (${run.run_id})`}
                    isSingleSample={run.samples === 1}
                  />
                </div>

                {/* Predictions Table */}
                <h4 style={{ fontSize: 15, fontWeight: 700, color: colors.textPrimary, marginBottom: 10 }}>Run Predictions Table</h4>
                <div style={{ overflowX: 'auto', border: `1px solid ${colors.cardBorder}`, borderRadius: 8 }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                    <thead>
                      <tr style={{ background: colors.tableHeaderBg, color: colors.textMuted }}>
                        {['Sample ID', 'Nutrient', 'Method', 'Calibration Source', 'Raw Pred', 'Final Pred', 'Actual', 'Error', 'Status'].map(h => (
                          <th key={h} style={{ padding: '8px 10px', textAlign: 'left', whiteSpace: 'nowrap' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {detail.predictions.map((p, idx) => {
                        const sc = STATUS_COLORS[p.status?.toUpperCase()] || '#64748b';
                        return (
                          <tr key={idx} style={{ borderBottom: `1px solid ${colors.tableBorder}`, background: idx % 2 === 0 ? colors.tableAltRow : 'transparent' }}>
                            <td style={{ padding: '6px 10px', fontWeight: 600, color: colors.textPrimary }}>{p.sample_id}</td>
                            <td style={{ padding: '6px 10px', fontWeight: 700, color: colors.accent }}>{p.nutrient}</td>
                            <td style={{ padding: '6px 10px', fontFamily: 'monospace', fontSize: 11, color: colors.textSecondary }}>{p.executed_method}</td>
                            <td style={{ padding: '6px 10px', color: colors.textMuted, fontSize: 11 }}>{p.calib_source}</td>
                            <td style={{ padding: '6px 10px', color: colors.textPrimary }}>{p.raw_pred != null ? parseFloat(p.raw_pred).toFixed(3) : 'N/A'}</td>
                            <td style={{ padding: '6px 10px', fontWeight: 700, color: colors.textPrimary }}>{p.final_pred != null ? parseFloat(p.final_pred).toFixed(3) : 'N/A'}</td>
                            <td style={{ padding: '6px 10px', color: colors.textSecondary }}>{p.actual != null ? parseFloat(p.actual).toFixed(3) : 'N/A'}</td>
                            <td style={{ padding: '6px 10px', fontWeight: 600, color: p.error != null ? (p.error < 0 ? '#dc2626' : '#16a34a') : colors.textMuted }}>
                              {p.error != null ? parseFloat(p.error).toFixed(3) : 'N/A'}
                            </td>
                            <td style={{ padding: '6px 10px' }}>
                              <span style={{ background: `${sc}20`, color: sc, borderRadius: 4, padding: '2px 6px', fontSize: 10, fontWeight: 700 }}>
                                {p.status || 'N/A'}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
