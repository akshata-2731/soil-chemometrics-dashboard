import React, { useState, useEffect } from 'react';
import axios from 'axios';
import * as XLSX from 'xlsx';
import { useTheme } from '../context/ThemeContext';
import { parseDataFile, ALL_TARGETS } from '../utils/fileParser';
import SpectralChart from '../components/SpectralChart';
import BatchSpectralChart from '../components/BatchSpectralChart';
import ActualVsPredictedChart from '../components/ActualVsPredictedChart';

const BASE = 'http://127.0.0.1:5000';

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
    <span style={{ background: `${c}20`, color: c, borderRadius: 4, padding: '2px 8px', fontSize: 11, fontWeight: 700 }}>
      {status || 'N/A'}
    </span>
  );
};

export default function ModeBatch() {
  const { colors } = useTheme();
  const [step, setStep] = useState(1);
  const [fileInfo, setFileInfo] = useState(null);
  const [samples, setSamples] = useState([]);
  const [columns, setColumns] = useState([]);
  const [selectedSampleId, setSelectedSampleId] = useState('');
  const [selectedNutrients, setSelectedNutrients] = useState([]);
  const [mapping, setMapping] = useState({});
  const [logics, setLogics] = useState([]);
  const [models, setModels] = useState([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [resultNutrient, setResultNutrient] = useState('OC');
  const [resultSampleId, setResultSampleId] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    axios.get(`${BASE}/api/logics`).then(r => setLogics(r.data)).catch(() => {});
    axios.get(`${BASE}/api/models`).then(r => setModels(r.data)).catch(() => {});
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setError('');
    try {
      const parsed = await parseDataFile(file);
      setFileInfo({
        fileName: parsed.fileName,
        sheetName: parsed.sheetName,
        sampleCount: parsed.sampleCount,
        columnCount: parsed.columnCount,
      });
      setSamples(parsed.samples);
      setColumns(parsed.columns);
      if (parsed.samples.length > 0) {
        setSelectedSampleId(parsed.samples[0].Sample_ID);
        setResultSampleId(parsed.samples[0].Sample_ID);
      }
      setStep(2);
    } catch (err) {
      setError('File parsing error: ' + err.message);
    }
  };

  const DEFAULT_LOGIC_MAP = {
    OC: 'M1', N: 'M2', P: 'M3', K: 'M4', Ca: 'M5', Mg: 'M6',
    S: 'M7', Fe: 'M8', Mn: 'M9', Cu: 'M10', Zn: 'M11', B: 'M12'
  };

  const toggleNutrient = (t) => {
    setSelectedNutrients(prev => {
      const exists = prev.includes(t);
      const next = exists ? prev.filter(x => x !== t) : [...prev, t];
      if (!exists && !mapping[t]) {
        setMapping(pm => ({
          ...pm,
          [t]: { method_type: 'logic', method_id: DEFAULT_LOGIC_MAP[t] || 'M1', calibration_required: true }
        }));
      }
      return next;
    });
  };

  const setAllNutrients = () => {
    setSelectedNutrients([...ALL_TARGETS]);
    const m = {};
    ALL_TARGETS.forEach(t => {
      m[t] = { method_type: 'logic', method_id: DEFAULT_LOGIC_MAP[t] || 'M1', calibration_required: true };
    });
    setMapping(m);
  };

  const updateMapping = (t, key, val) => {
    setMapping(prev => {
      const nextMap = { ...prev, [t]: { ...prev[t], [key]: val } };
      if (key === 'method_type') {
        if (val === 'ml') {
          const matching = models.find(m => m.id.toUpperCase().startsWith(t.toUpperCase()));
          nextMap[t].method_id = matching ? matching.id : (models.length ? models[0].id : '');
        } else {
          nextMap[t].method_id = DEFAULT_LOGIC_MAP[t] || (logics.length ? logics[0].id : 'M1');
        }
      }
      return nextMap;
    });
  };

  const runAnalysis = async () => {
    if (!samples.length) return setError('No samples loaded.');
    if (!selectedNutrients.length) return setError('Please select at least one nutrient.');

    setRunning(true);
    setError('');

    try {
      const r = await axios.post(`${BASE}/api/batch/predict`, {
        samples,
        targets: selectedNutrients,
        mapping
      });

      setResult(r.data);
      if (selectedNutrients.length > 0) {
        setResultNutrient(selectedNutrients[0]);
      }
      if (samples.length > 0) {
        setResultSampleId(samples[0].Sample_ID);
      }
      setShowResult(true);
    } catch (err) {
      setError('Prediction error: ' + (err.response?.data?.error || err.message));
    } finally {
      setRunning(false);
    }
  };

  
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

  const exportCSV = () => {
    if (!result) return;
    const headers = ['Sample ID', 'Nutrient', 'Selected Method', 'Executed Method', 'Calibration Source', 'Raw Prediction', 'Final Prediction', 'Actual', 'Error', 'Status'];
    const rows = result.results.map(r => [
      r.sample_id, r.nutrient, r.selected_method, r.executed_method,
      r.calibration_source, r.raw_prediction, r.final_prediction,
      r.actual ?? '', r.error ?? '', r.status
    ]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.run_id}_results.csv`;
    a.click();
  };

  const exportExcel = () => {
    if (!result) return;
    const data = result.results.map(r => ({
      'Sample ID': r.sample_id,
      'Nutrient': r.nutrient,
      'Selected Method': r.selected_method,
      'Executed Method': r.executed_method,
      'Calibration Source': r.calibration_source,
      'Raw Prediction': r.raw_prediction,
      'Final Prediction': r.final_prediction,
      'Actual': r.actual ?? 'N/A',
      'Error': r.error ?? 'N/A',
      'Status': r.status
    }));
    const worksheet = XLSX.utils.json_to_sheet(data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Batch Results');
    XLSX.writeFile(workbook, `${result.run_id}_results.xlsx`);
  };

  const currentInputSample = samples.find(s => s.Sample_ID === selectedSampleId) || samples[0];
  const currentResultSample = samples.find(s => s.Sample_ID === resultSampleId) || samples[0];

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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ fontSize: 24, fontWeight: 800, color: colors.textPrimary, margin: 0 }}>📊 Multiple Samples</h2>
      </div>

      {/* Step Indicator */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
        {['Upload File', 'Data Preview', 'Select Nutrients', 'Configure Methods', 'Run Analysis'].map((s, i) => {
          const active = step === i + 1;
          const done = step > i + 1;
          return (
            <div
              key={i}
              style={{
                padding: '8px 16px',
                borderRadius: 20,
                fontSize: 13,
                fontWeight: active ? 700 : 500,
                background: done ? `${colors.accent}18` : active ? colors.navLinkActiveBg : colors.cardBg,
                border: `1px solid ${active ? colors.accent : colors.cardBorder}`,
                color: done ? colors.accent : active ? colors.navLinkActive : colors.textMuted,
              }}
            >
              {i + 1}. {s}
            </div>
          );
        })}
      </div>

      {error && (
        <div style={{ background: '#ef444415', color: '#ef4444', border: '1px solid #ef444440', borderRadius: 8, padding: 14, marginBottom: 20, fontSize: 13 }}>
          {error}
        </div>
      )}

      {/* Step 1: Upload */}
      {step === 1 && (
        <div style={cardStyle}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: colors.accent, marginBottom: 12 }}>Step 1: Upload CSV / XLSX Data File</h3>
          <p style={{ color: colors.textSecondary, fontSize: 14, marginBottom: 20 }}>
            Upload a spreadsheet containing soil samples with 21 spectral wavelength columns (nm_410 to nm_200).
          </p>
          <div style={{ border: `2px dashed ${colors.cardBorder}`, borderRadius: 12, padding: 36, textAlign: 'center', background: colors.inputBg }}>
            <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileUpload} id="batch-file-input" style={{ display: 'none' }} />
            <label htmlFor="batch-file-input" style={btnStyle(colors.accent)}>
              📁 Select File (CSV / XLSX)
            </label>
            <p style={{ color: colors.textMuted, fontSize: 12, marginTop: 14, marginBotton: 0 }}>
              Parses `.xlsx` or `.csv` files natively using SheetJS without raw binary corruption.
            </p>
          </div>
        </div>
      )}

      {/* Step 2: Data Preview & Sample Spectral Input Graph */}
      {step >= 2 && fileInfo && (
        <div style={cardStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: colors.accent, margin: 0 }}>Step 2: File Data Summary & Preview</h3>
            <span style={{ fontSize: 13, fontWeight: 600, color: colors.textMuted }}>
              File: <strong style={{ color: colors.textPrimary }}>{fileInfo.fileName}</strong> ({fileInfo.sheetName})
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 20 }}>
            <div style={{ background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, padding: 12, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: colors.textMuted }}>Total Samples</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: colors.accent }}>{fileInfo.sampleCount}</div>
            </div>
            <div style={{ background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, padding: 12, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: colors.textMuted }}>Total Columns</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary }}>{fileInfo.columnCount}</div>
            </div>
            <div style={{ background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, padding: 12, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: colors.textMuted }}>Status</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#16a34a' }}>{fileInfo.sampleCount} Samples Loaded ✓</div>
            </div>
          </div>

          {/* GRAPH 1: Batch Spectral Input (All Samples) */}
          <BatchSpectralChart samples={samples} colors={colors} title={`Batch Spectral Input (Samples: ${samples.length})`} />

          {/* Data Preview Table */}
          <details style={{ marginTop: 12, marginBottom: 16 }}>
            <summary style={{ cursor: 'pointer', fontSize: 13, fontWeight: 600, color: colors.accent }}>
              Preview Raw Data Table ({samples.length} rows)
            </summary>
            <div style={{ overflowX: 'auto', marginTop: 10, border: `1px solid ${colors.cardBorder}`, borderRadius: 8 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ background: colors.tableHeaderBg, color: colors.textMuted }}>
                    {columns.slice(0, 15).map(c => (
                      <th key={c} style={{ padding: '8px 10px', textAlign: 'left', whiteSpace: 'nowrap' }}>{c}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {samples.slice(0, 5).map((row, idx) => (
                    <tr key={idx} style={{ borderBottom: `1px solid ${colors.tableBorder}` }}>
                      {columns.slice(0, 15).map(c => (
                        <td key={c} style={{ padding: '6px 10px', color: colors.textPrimary, whiteSpace: 'nowrap' }}>
                          {String(row[c] ?? '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>

          {step === 2 && (
            <button style={btnStyle(colors.accent)} onClick={() => setStep(3)}>
              Continue to Nutrient Selection &rarr;
            </button>
          )}
        </div>
      )}

      {/* Step 3: Select Nutrients */}
      {step >= 3 && (
        <div style={cardStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: colors.accent, margin: 0 }}>Step 3: Select Nutrients to Analyze</h3>
            <button style={btnStyle(colors.name === 'dark' ? '#334155' : '#cbd5e1', colors.textPrimary)} onClick={setAllNutrients}>
              Select All 12 Nutrients
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 10, marginBottom: 20 }}>
            {ALL_TARGETS.map(t => {
              const active = selectedNutrients.includes(t);
              return (
                <label
                  key={t}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    cursor: 'pointer',
                    background: active ? colors.navLinkActiveBg : colors.inputBg,
                    border: `1px solid ${active ? colors.accent : colors.cardBorder}`,
                    borderRadius: 8,
                    padding: '10px 14px',
                    fontSize: 14,
                    fontWeight: active ? 700 : 500,
                    color: active ? colors.accent : colors.textPrimary,
                    transition: 'all 0.15s',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={active}
                    onChange={() => toggleNutrient(t)}
                    style={{ accentColor: colors.accent, width: 16, height: 16 }}
                  />
                  {t}
                </label>
              );
            })}
          </div>

          {step === 3 && selectedNutrients.length > 0 && (
            <button style={btnStyle(colors.accent)} onClick={() => setStep(4)}>
              Configure Execution Methods &rarr;
            </button>
          )}
        </div>
      )}

      {/* Step 4: Configure Methods */}
      {step >= 4 && selectedNutrients.length > 0 && (
        <div style={cardStyle}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: colors.accent, marginBottom: 16 }}>Step 4: Configure Execution Methods</h3>
          <div style={{ overflowX: 'auto', marginBottom: 20 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: colors.tableHeaderBg, color: colors.textMuted, borderBottom: `1px solid ${colors.tableBorder}` }}>
                  <th style={{ textAlign: 'left', padding: '10px' }}>Nutrient</th>
                  <th style={{ textAlign: 'left', padding: '10px' }}>Method Type</th>
                  <th style={{ textAlign: 'left', padding: '10px' }}>Method Selection</th>
                  <th style={{ textAlign: 'left', padding: '10px', color: colors.accent }}>Automatic Rules (Calibration & Clamps)</th>
                </tr>
              </thead>
              <tbody>
                {selectedNutrients.map(t => (
                  <tr key={t} style={{ borderBottom: `1px solid ${colors.tableBorder}` }}>
                    <td style={{ padding: '10px', fontWeight: 700, color: colors.accent }}>{t}</td>
                    <td style={{ padding: '10px' }}>
                      <select
                        style={inputStyle}
                        value={mapping[t]?.method_type || 'logic'}
                        onChange={e => updateMapping(t, 'method_type', e.target.value)}
                      >
                        <option value="logic">Logic</option>
                        <option value="ml">ML Model</option>
                      </select>
                    </td>
                    <td style={{ padding: '10px' }}>
                      {mapping[t]?.method_type === 'ml' ? (
                        <select
                          style={inputStyle}
                          value={mapping[t]?.method_id || ''}
                          onChange={e => updateMapping(t, 'method_id', e.target.value)}
                        >
                          {models.map(m => (
                            <option key={m.id} value={m.id}>{m.id}</option>
                          ))}
                        </select>
                      ) : (
                        <select
                          style={inputStyle}
                          value={mapping[t]?.method_id || ''}
                          onChange={e => updateMapping(t, 'method_id', e.target.value)}
                        >
                          {logics.map(l => (
                            <option key={l.id} value={l.id}>{l.id} - {l.name}</option>
                          ))}
                        </select>
                      )}
                    </td>
                    <td style={{ padding: '10px', fontSize: 12, color: colors.textMuted }}>
                      <i>Determined by selected method automatically at execution</i>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {step === 4 && (
            <button style={btnStyle(colors.accent)} onClick={() => setStep(5)}>
              Proceed to Run &rarr;
            </button>
          )}
        </div>
      )}

      {/* Step 5: Run Analysis */}
      {step >= 5 && (
        <div style={cardStyle}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: colors.accent, marginBottom: 12 }}>Step 5: Run Batch Analysis</h3>
          <p style={{ color: colors.textSecondary, fontSize: 14, marginBottom: 20 }}>
            Ready: Executing <strong style={{ color: colors.accent }}>{samples.length} samples</strong> across <strong style={{ color: colors.accent }}>{selectedNutrients.length} nutrients</strong>.
          </p>
          <button style={{ ...btnStyle('#16a34a'), fontSize: 16, padding: '14px 36px' }} onClick={runAnalysis} disabled={running}>
            {running ? 'Running Analysis...' : '▶ RUN BATCH ANALYSIS'}
          </button>
        </div>
      )}

      {/* SEPARATE BATCH RESULTS MODAL / PANEL */}
      {showResult && result && (
        <div style={{ position: 'fixed', inset: 0, background: colors.modalOverlay, zIndex: 1000, overflow: 'auto', display: 'flex', justifyContent: 'center', padding: 20 }}>
          <div style={{ position: 'relative', zIndex: 1001, background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 16, padding: 30, width: '95%', maxWidth: 1150, marginTop: 20, marginBottom: 40, boxShadow: colors.cardShadow }}>
            
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24, borderBottom: `1px solid ${colors.cardBorder}`, paddingBottom: 16 }}>
              <div>
                <h2 style={{ fontSize: 24, fontWeight: 800, color: colors.textPrimary, margin: 0 }}>Batch Analysis Results</h2>
                <div style={{ color: colors.accent, fontSize: 14, fontWeight: 700, marginTop: 4 }}>
                  Run ID: {result.run_id}
                </div>
                <div style={{ color: colors.textMuted, fontSize: 12, marginTop: 2 }}>
                  Samples: {samples.length} | Nutrients: {selectedNutrients.length} | Predictions: {result.results.length}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button style={btnStyle(colors.name === 'dark' ? '#334155' : '#cbd5e1', colors.textPrimary)} onClick={exportCSV}>Export CSV</button>
                <button style={btnStyle(colors.name === 'dark' ? '#334155' : '#cbd5e1', colors.textPrimary)} onClick={exportExcel}>Export Excel</button>
                <button style={btnStyle('#dc2626')} onClick={() => setShowResult(false)}>Close</button>
              </div>
            </div>

            {/* GRAPH 1: SAMPLE SPECTRAL INPUT */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <label style={{ fontSize: 13, fontWeight: 700, color: colors.textPrimary }}>Sample Selector for Spectral Graph:</label>
                <select
                  style={{ ...inputStyle, width: 220 }}
                  value={resultSampleId}
                  onChange={e => setResultSampleId(e.target.value)}
                >
                  {samples.map(s => (
                    <option key={s.Sample_ID} value={s.Sample_ID}>{s.Sample_ID}</option>
                  ))}
                </select>
              </div>
              <SpectralChart sampleData={currentResultSample} colors={colors} title="Sample Spectral Input" />
            </div>

            {/* GRAPH 2: ACTUAL VS PREDICTED */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <label style={{ fontSize: 13, fontWeight: 700, color: colors.textPrimary }}>Nutrient Selector (Graph & Table Filter):</label>
                <select
                  style={{ ...inputStyle, width: 180 }}
                  value={resultNutrient}
                  onChange={e => setResultNutrient(e.target.value)}
                >
                  {selectedNutrients.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <ActualVsPredictedChart results={result.results} selectedNutrient={resultNutrient} colors={colors} title="Actual vs Predicted" />
            </div>

            
              {/* METRICS SUMMARY */}
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

              {/* Results Table */}

            <h4 style={{ fontSize: 16, fontWeight: 700, color: colors.textPrimary, marginBottom: 12 }}>Detailed Results Table</h4>
            <div style={{ 
              overflowX: 'auto', 
              overflowY: 'auto', 
              maxHeight: 600, 
              background: colors.cardBg, 
              border: `1px solid ${colors.cardBorder}`, 
              borderRadius: 8 
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, minWidth: 800 }}>
                <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                  <tr style={{ background: colors.tableHeaderBg, color: colors.textPrimary, boxShadow: `0 1px 0 ${colors.tableBorder}` }}>
                    {['Sample ID', 'Nutrient', 'Method', 'Calibration Source', 'Raw Pred', 'Final Pred', 'Actual', 'Error', 'Status'].map(h => (
                      <th key={h} style={{ padding: '14px 12px', textAlign: 'left', whiteSpace: 'nowrap', fontWeight: 700 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody style={{ background: colors.cardBg }}>
                  {result.results.filter(r => r.nutrient === resultNutrient).map((r, idx) => (
                    <tr key={idx} style={{ borderBottom: `1px solid ${colors.tableBorder}`, background: idx % 2 === 0 ? colors.tableAltRow : 'transparent' }}>
                      <td style={{ padding: '12px', fontWeight: 600, color: colors.textPrimary, whiteSpace: 'nowrap' }}>{r.sample_id}</td>
                      <td style={{ padding: '12px', fontWeight: 700, color: colors.accent, whiteSpace: 'nowrap' }}>{r.nutrient}</td>
                      <td style={{ padding: '12px', fontFamily: 'monospace', fontSize: 12, color: colors.textSecondary, whiteSpace: 'nowrap' }}>{r.executed_method}</td>
                      <td style={{ padding: '12px', color: colors.textMuted, fontSize: 12, whiteSpace: 'nowrap' }}>{r.calibration_source}</td>
                      <td style={{ padding: '12px', color: colors.textPrimary, whiteSpace: 'nowrap' }}>{r.raw_prediction != null ? r.raw_prediction.toFixed(3) : 'N/A'}</td>
                      <td style={{ padding: '12px', fontWeight: 700, color: colors.textPrimary, whiteSpace: 'nowrap' }}>{r.final_prediction != null ? r.final_prediction.toFixed(3) : 'N/A'}</td>
                      <td style={{ padding: '12px', color: colors.textSecondary, whiteSpace: 'nowrap' }}>{r.actual != null ? r.actual.toFixed(3) : 'N/A'}</td>
                      <td style={{ padding: '12px', fontWeight: 600, color: r.error != null ? (r.error < 0 ? '#dc2626' : '#16a34a') : colors.textMuted, whiteSpace: 'nowrap' }}>
                        {r.error != null ? r.error.toFixed(3) : 'N/A'}
                      </td>
                      <td style={{ padding: '12px', whiteSpace: 'nowrap' }}>{badge(r.status)}</td>
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
