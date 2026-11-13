import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTheme } from '../context/ThemeContext';
import { WAVELENGTH_ORDER, ALL_TARGETS, parseDataFile } from '../utils/fileParser';
import SpectralChart from '../components/SpectralChart';
import ActualVsPredictedChart from '../components/ActualVsPredictedChart';

const BASE = import.meta.env.BASE_URL.replace(/\/$/, '');

const badge = (status) => {
  const colors = { 
    HIGH: '#16a34a', 
    ADEQUATE: '#16a34a', 
    LOW: '#dc2626', 
    DEFICIENT: '#dc2626', 
    MEDIUM: '#ca8a04' 
  };
  const c = colors[status?.toUpperCase()] || '#64748b';
  return (
    <span style={{ background: `${c}20`, color: c, borderRadius: 4, padding: '3px 10px', fontSize: 12, fontWeight: 700 }}>
      {status || 'N/A'}
    </span>
  );
};

export default function ModeSingle() {
  const { colors } = useTheme();
  const [sampleId, setSampleId] = useState('S001');
  const [wvs, setWvs] = useState(Object.fromEntries(WAVELENGTH_ORDER.map(w => [w, ''])));
  const [target, setTarget] = useState('OC');
  const [methodType, setMethodType] = useState('logic');
  const [methodId, setMethodId] = useState('');
  const [calRequired, setCalRequired] = useState(true);
  const [logics, setLogics] = useState([]);
  const [models, setModels] = useState([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [showTrace, setShowTrace] = useState(false);

  useEffect(() => {
    axios.get(`${BASE}/api/logics`).then(r => { 
      setLogics(r.data); 
      if (!methodId && r.data.length) setMethodId(r.data[0].id); 
    }).catch(() => {});
    axios.get(`${BASE}/api/models`).then(r => setModels(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (methodType === 'logic' && logics.length) setMethodId(logics[0].id);
    if (methodType === 'ml') {
      const matching = models.find(m => m.id.toUpperCase().startsWith(target.toUpperCase()));
      if (matching) setMethodId(matching.id);
      else if (models.length) setMethodId(models[0].id);
    }
  }, [methodType, target]);

  const setWv = (w, v) => setWvs(prev => ({ ...prev, [w]: v }));

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

  const runPrediction = async () => {
    setRunning(true);
    setError('');
    setResult(null);

    const sampleObj = { Sample_ID: sampleId };
    WAVELENGTH_ORDER.forEach(w => {
      sampleObj[`nm_${w}`] = parseFloat(wvs[w]) || 0;
    });

    try {
      const r = await axios.post(`${BASE}/api/single/predict`, {
        samples: [sampleObj],
        targets: [target],
        mapping: {
          [target]: { method_type: methodType, method_id: methodId, calibration_required: calRequired }
        }
      });
      setResult(r.data);
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

  const res = result?.results?.[0];

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 800, color: colors.textPrimary, marginBottom: 20 }}>🎯 Single Nutrient Analysis</h2>

      {error && (
        <div style={{ background: '#ef444415', color: '#ef4444', border: '1px solid #ef444440', borderRadius: 8, padding: 14, marginBottom: 20, fontSize: 13 }}>
          {error}
        </div>
      )}

      {/* Sample ID & Fill Options */}
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

      {/* Spectral Input Curve Graph */}
      <SpectralChart sampleData={currentSampleObj} colors={colors} title="Sample Spectral Input Graph" />

      {/* Method & Nutrient Configuration */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: colors.accent, marginBottom: 16 }}>Nutrient & Execution Method</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          <div>
            <label style={{ color: colors.textSecondary, fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 6 }}>Target Nutrient</label>
            <select style={inputStyle} value={target} onChange={e => setTarget(e.target.value)}>
              {ALL_TARGETS.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label style={{ color: colors.textSecondary, fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 6 }}>Method Type</label>
            <div style={{ display: 'flex', gap: 10 }}>
              {['logic', 'ml'].map(mt => (
                <label key={mt} style={{
                  display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer',
                  background: methodType === mt ? colors.navLinkActiveBg : colors.inputBg,
                  border: `1px solid ${methodType === mt ? colors.accent : colors.cardBorder}`,
                  borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: methodType === mt ? 700 : 500
                }}>
                  <input type="radio" name="mt" checked={methodType === mt} onChange={() => setMethodType(mt)} style={{ accentColor: colors.accent }} />
                  {mt === 'logic' ? 'Logic' : 'ML Model'}
                </label>
              ))}
            </div>
          </div>
          <div>
            <label style={{ color: colors.textSecondary, fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 6 }}>
              {methodType === 'logic' ? 'Logic Selection' : 'ML Model Selection'}
            </label>
            <select style={inputStyle} value={methodId} onChange={e => setMethodId(e.target.value)}>
              {methodType === 'logic'
                ? logics.map(l => <option key={l.id} value={l.id}>{l.id} – {l.name}</option>)
                : models.map(m => <option key={m.id} value={m.id}>{m.id}</option>)
              }
            </select>
          </div>
          <div>
            <label style={{ color: colors.textSecondary, fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 6 }}>
              Automatic Rules
            </label>
            <div style={{ marginTop: 6, fontSize: 12, color: colors.textMuted }}>
              <i>Calibration & Clamps automatically determined by method</i>
            </div>
          </div>
        </div>

        <button style={{ ...btnStyle(colors.accent), marginTop: 24, fontSize: 16, padding: '12px 32px' }} onClick={runPrediction} disabled={running}>
          {running ? 'Running Prediction...' : '▶ RUN SINGLE PREDICTION'}
        </button>
      </div>

      {/* RESULTS DISPLAY */}
      {res && (
        <div style={{ ...cardStyle, border: `1.5px solid ${res.executed_method === 'ERROR' ? '#dc2626' : '#16a34a'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 10 }}>
            <div>
              <h3 style={{ color: res.executed_method === 'ERROR' ? '#dc2626' : colors.accent, fontSize: 20, margin: 0, marginBottom: 4 }}>
                Prediction Result — {res.nutrient}
              </h3>
              <div style={{ color: colors.textMuted, fontSize: 12 }}>Run ID: {result.run_id}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 36, fontWeight: 800, color: colors.textPrimary }}>
                {res.final_prediction != null ? res.final_prediction.toFixed(3) : (res.status && res.status.includes('INCOMPLETE') ? 'INCOMPLETE' : 'ERROR')}
              </div>
              {badge(res.status)}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginTop: 20 }}>
            {[
              ['Selected Method', res.selected_method],
              ['Executed Method', res.executed_method],
              ['Method Type', res.method_type],
              ['Calibration', res.calibration_required ? 'Required' : 'Not Required'],
              ['Actual', res.actual != null ? res.actual.toFixed(3) : 'N/A'],
              ['Error', res.error != null ? res.error.toFixed(3) : 'N/A'],
            ].map(([k, v]) => (
              <div key={k} style={{ background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: 12 }}>
                <div style={{ color: colors.textMuted, fontSize: 11, marginBottom: 4 }}>{k}</div>
                <div style={{ color: colors.textPrimary, fontWeight: 700, fontSize: 14 }}>{v}</div>
              </div>
            ))}
          </div>

          {/* Actual vs Predicted Graph 2 */}
          <div style={{ marginTop: 24 }}>
            <ActualVsPredictedChart 
              results={result.results} 
              selectedNutrient={res.nutrient} 
              colors={colors} 
              title="Actual vs Predicted Comparison"
              isSingleSample={true}
            />
          </div>

          {/* Trace Details Collapsible */}
          <button
            style={{ ...btnStyle(colors.name === 'dark' ? '#334155' : '#cbd5e1', colors.textPrimary), marginTop: 16, padding: '8px 16px', fontSize: 12 }}
            onClick={() => setShowTrace(!showTrace)}
          >
            {showTrace ? '▲ Hide' : '▼ Show'} Detailed Execution Trace
          </button>

          {showTrace && (
            <div style={{ marginTop: 14, background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: 16 }}>
              
              {/* Dynamically render Detailed Calculation Steps from the Python script */}
              {res.detailed_steps && Object.keys(res.detailed_steps).length > 0 && (
                <div style={{ marginBottom: 16, paddingBottom: 16, borderBottom: `1px dashed ${colors.cardBorder}` }}>
                  <h4 style={{ color: colors.accent, fontSize: 13, marginBottom: 12, marginTop: 0 }}>Detailed Python Execution Trace</h4>
                  {Object.entries(res.detailed_steps).map(([stepName, stepVal]) => (
                    <div key={stepName} style={{ marginBottom: 8 }}>
                      <div style={{ color: colors.textMuted, fontSize: 11, fontWeight: 700 }}>{stepName.toUpperCase()}</div>
                      <div style={{ color: stepName === 'error' ? '#ef4444' : colors.textPrimary, fontSize: 12, fontFamily: 'monospace', background: colors.name === 'dark' ? '#1e293b' : '#f1f5f9', padding: '6px 10px', borderRadius: 4, marginTop: 2 }}>{stepVal}</div>
                    </div>
                  ))}
                </div>
              )}

              {[
                ['Required IPS', Array.isArray(res.required_ips) && res.required_ips.length > 0 ? res.required_ips.join(', ') : 'None'],
                ['Calibration Source', res.calibration_source],
                ['Wavelengths Used', Array.isArray(res.wavelengths_used) ? res.wavelengths_used.join(', ') : 'N/A'],
                ['Raw Prediction', res.raw_prediction != null ? res.raw_prediction.toFixed(4) : 'N/A'],
                ['Clamp Applied', res.clamp_applied ? 'Yes' : 'No'],
                ['Clamp Rule', res.clamp_rule],
                ['Final Prediction', res.final_prediction != null ? res.final_prediction.toFixed(4) : 'N/A'],
                ['Status Classification', res.status],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', gap: 12, padding: '6px 0', borderBottom: `1px solid ${colors.cardBorder}` }}>
                  <span style={{ color: colors.textMuted, minWidth: 170, fontSize: 12, fontWeight: 600 }}>{k}</span>
                  <span style={{ color: colors.textPrimary, fontSize: 12 }}>{v}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
