import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTheme } from '../context/ThemeContext';
import { WAVELENGTH_ORDER, ALL_TARGETS, parseDataFile } from '../utils/fileParser';
import SpectralChart from '../components/SpectralChart';
import ActualVsPredictedChart from '../components/ActualVsPredictedChart';

const BASE = 'http://127.0.0.1:5000';

const STATUS_COLORS = { 
  HIGH: '#16a34a', 
  ADEQUATE: '#16a34a', 
  LOW: '#dc2626', 
  DEFICIENT: '#dc2626', 
  MEDIUM: '#ca8a04' 
};

export default function ModeAll12() {
  const { colors } = useTheme();
  const [sampleId, setSampleId] = useState('S001');
  const [wvs, setWvs] = useState(Object.fromEntries(WAVELENGTH_ORDER.map(w => [w, ''])));
  const [config, setConfig] = useState(
    Object.fromEntries(ALL_TARGETS.map(t => [t, { method_type: 'logic', method_id: 'M1', calibration_required: true }]))
  );
  const [sameForAll, setSameForAll] = useState(false);
  const [globalMethod, setGlobalMethod] = useState({ method_type: 'logic', method_id: 'M1', calibration_required: true });
  const [logics, setLogics] = useState([]);
  const [models, setModels] = useState([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [resultNutrient, setResultNutrient] = useState('OC');
  const [error, setError] = useState('');

  useEffect(() => {
    axios.get(`${BASE}/api/logics`).then(r => {
      setLogics(r.data);
      if (r.data.length) {
        setConfig(cfg => Object.fromEntries(ALL_TARGETS.map(t => [t, { ...cfg[t], method_id: r.data[0].id }])));
        setGlobalMethod(g => ({ ...g, method_id: r.data[0].id }));
      }
    }).catch(() => {});
    axios.get(`${BASE}/api/models`).then(r => setModels(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (sameForAll) {
      setConfig(Object.fromEntries(ALL_TARGETS.map(t => [t, { ...globalMethod }])));
    }
  }, [sameForAll, globalMethod]);

  const setWv = (w, v) => setWvs(prev => ({ ...prev, [w]: v }));
  const updateConfig = (t, k, v) => {
    setConfig(prev => {
      const next = { ...prev, [t]: { ...prev[t], [k]: v } };
      if (k === 'method_type') {
        if (v === 'ml') {
          const matching = models.find(m => m.id.toUpperCase().startsWith(t.toUpperCase()));
          next[t].method_id = matching ? matching.id : (models.length ? models[0].id : '');
        } else {
          next[t].method_id = logics.length ? logics[0].id : 'M1';
        }
      }
      return next;
    });
  };

  const loadDemo = () => {
    const demo = { 410: 1709.45, 435: 385.95, 460: 1471.25, 485: 459.0, 510: 676.55, 535: 932.51, 560: 396.79, 585: 414.76, 610: 249.78, 645: 66.14, 680: 38.78, 705: 22.27, 730: 1068.26, 760: 256.03, 810: 88.32, 860: 52.27, 900: 83.07, 940: 348.53, 320: 65.41, 280: 1.83, 200: 3.11 };
    setWvs(Object.fromEntries(WAVELENGTH_ORDER.map(w => [w, demo[w] ?? 0])));
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const parsed = await parseDataFile(file);
      if (parsed.samples.length > 0) {
        const s = parsed.samples[0];
        setSampleId(s.Sample_ID);
        const nextWvs = {};
        WAVELENGTH_ORDER.forEach(w => {
          nextWvs[w] = s[`nm_${w}`] ?? s[String(w)] ?? 0;
        });
        setWvs(nextWvs);
      }
    } catch (err) {
      setError('File loading error: ' + err.message);
    }
  };

  const runAll12 = async () => {
    setRunning(true);
    setError('');
    setResult(null);

    const sampleObj = { Sample_ID: sampleId };
    WAVELENGTH_ORDER.forEach(w => {
      sampleObj[`nm_${w}`] = parseFloat(wvs[w]) || 0;
    });

    try {
      const r = await axios.post(`${BASE}/api/all12/predict`, {
        samples: [sampleObj],
        targets: ALL_TARGETS,
        mapping: config
      });
      setResult(r.data);
      setShowResult(true);
    } catch (err) {
      setError('Prediction error: ' + (err.response?.data?.error || err.message));
    } finally {
      setRunning(false);
    }
  };

  const currentSampleObj = {
    Sample_ID: sampleId,
    ...Object.fromEntries(WAVELENGTH_ORDER.map(w => [`nm_${w}`, parseFloat(wvs[w]) || 0]))
  };

  const cardStyle = {
    background: colors.cardBg,
    border: `1px solid ${colors.cardBorder}`,
    borderRadius: 12,
    padding: 24,
    marginBottom: 20,
    boxShadow: colors.cardShadow,
  };

  const btnStyle = (bg = colors.accent, textColor = '#ffffff') => ({
    background: bg,
    color: textColor,
    border: 'none',
    borderRadius: 8,
    padding: '10px 20px',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 14,
    transition: 'all 0.15s',
  });

  const inputStyle = {
    background: colors.inputBg,
    color: colors.inputColor,
    border: `1px solid ${colors.inputBorder}`,
    borderRadius: 6,
    padding: '8px 12px',
    fontSize: 13,
    width: '100%',
  };

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 800, color: colors.textPrimary, marginBottom: 20 }}>🌱 Single Sample — All 12 Nutrients</h2>

      {error && (
        <div style={{ background: '#ef444415', color: '#ef4444', border: '1px solid #ef444440', borderRadius: 8, padding: 14, marginBottom: 20, fontSize: 13 }}>
          {error}
        </div>
      )}

      {/* Sample ID & File Load */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: colors.accent, margin: 0 }}>Sample Identification</h3>
          <div style={{ display: 'flex', gap: 10 }}>
            <label style={{ ...btnStyle(colors.name === 'dark' ? '#334155' : '#cbd5e1', colors.textPrimary), display: 'inline-block', cursor: 'pointer', fontSize: 12, padding: '6px 12px' }}>
              📁 Load Sample from File
              <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileUpload} style={{ display: 'none' }} />
            </label>
            <button style={{ ...btnStyle(colors.name === 'dark' ? '#334155' : '#cbd5e1', colors.textPrimary), fontSize: 12, padding: '6px 12px' }} onClick={loadDemo}>
              Load Demo Values
            </button>
          </div>
        </div>
        <input
          style={{ ...inputStyle, maxWidth: 240 }}
          value={sampleId}
          onChange={e => setSampleId(e.target.value)}
          placeholder="e.g. S001"
        />
      </div>

      {/* 21 Wavelength Inputs */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: colors.accent, marginBottom: 16 }}>21 Spectral Wavelength Inputs (nm)</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 10 }}>
          {WAVELENGTH_ORDER.map(w => (
            <div key={w}>
              <label style={{ color: colors.textMuted, fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                nm_{w}
              </label>
              <input
                style={inputStyle}
                type="number"
                value={wvs[w]}
                onChange={e => setWv(w, e.target.value)}
                placeholder="0"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Spectral Input Graph 1 */}
      <SpectralChart sampleData={currentSampleObj} colors={colors} title="Sample Spectral Input Graph" />

      {/* Method Configuration */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: colors.accent, margin: 0 }}>Configure 12 Nutrient Execution Methods</h3>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, fontWeight: 600, color: colors.textPrimary }}>
            <input type="checkbox" checked={sameForAll} onChange={e => setSameForAll(e.target.checked)} style={{ accentColor: colors.accent, width: 16, height: 16 }} />
            Same method for all 12 nutrients
          </label>
        </div>

        {sameForAll && (
          <div style={{ background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: 16, marginBottom: 16, display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
            <select style={{ ...inputStyle, width: 'auto' }} value={globalMethod.method_type} onChange={e => setGlobalMethod(g => ({ ...g, method_type: e.target.value }))}>
              <option value="logic">Logic</option>
              <option value="ml">ML Model</option>
            </select>
            <select style={{ ...inputStyle, width: 260 }} value={globalMethod.method_id} onChange={e => setGlobalMethod(g => ({ ...g, method_id: e.target.value }))}>
              {globalMethod.method_type === 'logic'
                ? logics.map(l => <option key={l.id} value={l.id}>{l.id} – {l.name}</option>)
                : models.map(m => <option key={m.id} value={m.id}>{m.id}</option>)
              }
            </select>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: colors.textMuted }}>
              <i>Calibration automatically determined</i>
            </div>
          </div>
        )}

        {!sameForAll && (
          <div style={{ overflowX: 'auto', marginBottom: 16 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: colors.tableHeaderBg, color: colors.textMuted, borderBottom: `1px solid ${colors.tableBorder}` }}>
                  <th style={{ padding: '8px 10px', textAlign: 'left' }}>Nutrient</th>
                  <th style={{ padding: '8px 10px', textAlign: 'left' }}>Type</th>
                  <th style={{ padding: '8px 10px', textAlign: 'left' }}>Method</th>
                  <th style={{ padding: '8px 10px', textAlign: 'left', color: colors.accent }}>Automatic Rules</th>
                </tr>
              </thead>
              <tbody>
                {ALL_TARGETS.map(t => (
                  <tr key={t} style={{ borderBottom: `1px solid ${colors.tableBorder}` }}>
                    <td style={{ padding: '8px 10px', fontWeight: 700, color: colors.accent }}>{t}</td>
                    <td style={{ padding: '8px 10px' }}>
                      <select style={inputStyle} value={config[t].method_type} onChange={e => updateConfig(t, 'method_type', e.target.value)}>
                        <option value="logic">Logic</option>
                        <option value="ml">ML Model</option>
                      </select>
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      <select style={inputStyle} value={config[t].method_id} onChange={e => updateConfig(t, 'method_id', e.target.value)}>
                        {config[t].method_type === 'logic'
                          ? logics.map(l => <option key={l.id} value={l.id}>{l.id} – {l.name}</option>)
                          : models.map(m => <option key={m.id} value={m.id}>{m.id}</option>)
                        }
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <button style={{ ...btnStyle('#16a34a'), marginTop: 16, fontSize: 16, padding: '14px 36px' }} onClick={runAll12} disabled={running}>
          {running ? 'Running All 12 Nutrients...' : '▶ RUN ALL 12 NUTRIENTS'}
        </button>
      </div>

      {/* RESULTS DISPLAY */}
      {showResult && result && (
        <div style={{ position: 'fixed', inset: 0, background: colors.modalOverlay, zIndex: 1000, overflow: 'auto', display: 'flex', justifyContent: 'center', padding: 20 }}>
          <div style={{ position: 'relative', zIndex: 1001, background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 16, padding: 30, width: '95%', maxWidth: 1100, marginTop: 20, marginBottom: 40, boxShadow: colors.cardShadow }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, borderBottom: `1px solid ${colors.cardBorder}`, paddingBottom: 16 }}>
              <div>
                <h2 style={{ fontSize: 24, fontWeight: 800, color: colors.textPrimary, margin: 0 }}>All 12 Nutrients Results</h2>
                <div style={{ color: colors.accent, fontSize: 14, fontWeight: 700, marginTop: 4 }}>Run ID: {result.run_id}</div>
                <div style={{ color: colors.textMuted, fontSize: 12 }}>Sample ID: {sampleId}</div>
              </div>
              <button style={btnStyle('#dc2626')} onClick={() => setShowResult(false)}>Close</button>
            </div>

            {/* 12 Result Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, marginBottom: 24 }}>
              {result.results.map(r => {
                const sc = STATUS_COLORS[r.status?.toUpperCase()] || '#64748b';
                return (
                  <div key={r.nutrient} style={{ background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 10, padding: 14 }}>
                    <div style={{ color: colors.textMuted, fontSize: 11, fontWeight: 600 }}>{r.nutrient}</div>
                    <div style={{ fontSize: 24, fontWeight: 800, color: sc, margin: '4px 0' }}>
                      {r.final_prediction != null ? r.final_prediction.toFixed(2) : 'ERR'}
                    </div>
                    <div style={{ color: colors.textMuted, fontSize: 10, fontFamily: 'monospace', marginBottom: 4 }}>{r.executed_method}</div>
                    <span style={{ background: `${sc}20`, color: sc, borderRadius: 4, padding: '2px 6px', fontSize: 10, fontWeight: 700 }}>
                      {r.status || 'N/A'}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Nutrient Selector & Graph 2 */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <label style={{ fontSize: 13, fontWeight: 700, color: colors.textPrimary }}>Nutrient Selector for Output Graph:</label>
                <select
                  style={{ ...inputStyle, width: 180 }}
                  value={resultNutrient}
                  onChange={e => setResultNutrient(e.target.value)}
                >
                  {ALL_TARGETS.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <ActualVsPredictedChart 
                results={result.results} 
                selectedNutrient={resultNutrient} 
                colors={colors} 
                title="Actual vs Predicted Comparison"
                isSingleSample={true}
              />
            </div>

            {/* Detail Table */}
            <h4 style={{ fontSize: 16, fontWeight: 700, color: colors.textPrimary, marginBottom: 12 }}>Results Summary Table</h4>
            <div style={{ overflowX: 'auto', border: `1px solid ${colors.cardBorder}`, borderRadius: 8, background: colors.cardBg }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ background: colors.tableHeaderBg, color: colors.textMuted }}>
                    {['Nutrient', 'Method', 'Calib Source', 'Raw Pred', 'Final Pred', 'Actual', 'Error', 'Status'].map(h => (
                      <th key={h} style={{ padding: '8px 10px', textAlign: 'left' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.results.map((r, i) => (
                    <tr key={i} style={{ borderBottom: `1px solid ${colors.tableBorder}`, background: i % 2 === 0 ? colors.tableAltRow : colors.cardBg }}>
                      <td style={{ padding: '8px 10px', fontWeight: 700, color: colors.accent }}>{r.nutrient}</td>
                      <td style={{ padding: '8px 10px', fontFamily: 'monospace', fontSize: 11, color: colors.textSecondary }}>{r.executed_method}</td>
                      <td style={{ padding: '8px 10px', color: colors.textMuted, fontSize: 11 }}>{r.calibration_source}</td>
                      <td style={{ padding: '8px 10px', color: colors.textPrimary }}>{r.raw_prediction != null ? r.raw_prediction.toFixed(3) : 'N/A'}</td>
                      <td style={{ padding: '8px 10px', fontWeight: 700, color: colors.textPrimary }}>{r.final_prediction != null ? r.final_prediction.toFixed(3) : 'N/A'}</td>
                      <td style={{ padding: '8px 10px', color: colors.textSecondary }}>{r.actual != null ? r.actual.toFixed(3) : 'N/A'}</td>
                      <td style={{ padding: '8px 10px', fontWeight: 600, color: r.error != null ? (r.error < 0 ? '#dc2626' : '#16a34a') : colors.textMuted }}>
                        {r.error != null ? r.error.toFixed(3) : 'N/A'}
                      </td>
                      <td style={{ padding: '8px 10px' }}>
                        {(() => {
                          const sc = STATUS_COLORS[r.status?.toUpperCase()] || '#64748b';
                          return <span style={{ background: `${sc}20`, color: sc, borderRadius: 4, padding: '2px 6px', fontSize: 11, fontWeight: 700 }}>{r.status || 'N/A'}</span>;
                        })()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
