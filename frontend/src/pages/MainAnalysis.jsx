import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, CheckSquare, Activity, Settings, Play, BarChart2, History, CheckCircle, ArrowLeft, FileText, Target, Layers, X, Download } from 'lucide-react';
import { ScatterChart, Scatter, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const WAVELENGTHS_ORDER = [410,435,460,485,510,535,560,585,610,645,680,705,730,760,810,860,900,940,320,280,200];
const TARGETS = ['OC', 'N', 'P', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Mn', 'Cu', 'Zn', 'B'];

function MainAnalysis() {
  const [logics, setLogics] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // High-level Mode Selection
  // null | 'MODE1' | 'MODE2' | 'MODE3'
  const [mode, setMode] = useState(null);

  // Common Mapping State (used by all modes)
  const [mapping, setMapping] = useState({});
  const [selectedTargets, setSelectedTargets] = useState({});
  
  // Wavelength Inputs (Mode 2 & 3)
  const [wvs, setWvs] = useState(WAVELENGTHS_ORDER.reduce((acc, curr) => ({ ...acc, [curr]: '' }), {}));
  const [singleSampleId, setSingleSampleId] = useState('SAMPLE_01');

  // Mode 2 specific state
  const [mode2Target, setMode2Target] = useState('OC');

  // Mode 1 specific state
  const [batchSamples, setBatchSamples] = useState([]);
  const [fileInfo, setFileInfo] = useState(null);

  // Results & Popups
  const [processing, setProcessing] = useState(false);
  const [activePopup, setActivePopup] = useState(null); // 'MODE1', 'MODE2', 'MODE3'
  const [resultsData, setResultsData] = useState([]);
  const [runMetadata, setRunMetadata] = useState({});

  useEffect(() => {
    axios.get(import.meta.env.BASE_URL + 'api/config/logics').then(resLogics => {
      setLogics(resLogics.data.logics || []);
      // Setup Defaults
      const defTargets = {};
      const defMap = {};
      TARGETS.forEach(t => {
        defTargets[t] = true;
        defMap[t] = { method_type: 'ml', method_id: `${t}_model.pkl`, calibration_required: false };
      });
      setSelectedTargets(defTargets);
      setMapping(defMap);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleChangeMapping = (t, field, val) => {
    setMapping(prev => {
      const cur = prev[t] || {};
      const next = { ...cur, [field]: val };
      if (field === 'method_id') {
        next.method_type = val.endsWith('.pkl') ? 'ml' : 'logic';
        next.calibration_required = (next.method_type === 'logic'); 
      }
      return { ...prev, [t]: next };
    });
  };

  const loadDemoWavelengths = () => {
    const demo = {};
    WAVELENGTHS_ORDER.forEach(nm => demo[nm] = (Math.random() * 2).toFixed(3));
    setWvs(demo);
  };

  const parseCSV = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const rows = evt.target.result.split('\n');
      if (rows.length < 2) return;
      const headers = rows[0].split(',').map(s => s.trim().replace(/\r/g, ''));
      const parsed = [];
      let wvCount = 0; let actualCount = 0;
      headers.forEach(h => {
        if (h.startsWith('nm_') || !isNaN(parseFloat(h))) wvCount++;
        if (TARGETS.some(t => h.includes(t))) actualCount++;
      });
      for (let i=1; i<rows.length; i++) {
        if (!rows[i].trim()) continue;
        const cols = rows[i].split(',');
        let rowObj = {};
        headers.forEach((h, idx) => { rowObj[h] = cols[idx] ? cols[idx].trim().replace(/\r/g, '') : ''; });
        parsed.push(rowObj);
      }
      setBatchSamples(parsed);
      setFileInfo({ name: f.name, samples: parsed.length, wvs: wvCount, actuals: actualCount });
    };
    reader.readAsText(f);
  };

  // -------------------------------------------------------------
  // EXECUTION WRAPPERS
  // -------------------------------------------------------------

  const runMode1 = async () => {
    const targetsToRun = TARGETS.filter(t => selectedTargets[t]);
    if (batchSamples.length === 0) return alert("Upload a file first.");
    if (targetsToRun.length === 0) return alert("Select at least one nutrient.");
    
    setProcessing(true);
    const runId = 'RUN-' + Math.random().toString(36).substr(2, 6).toUpperCase();
    
    try {
      const res = await axios.post(import.meta.env.BASE_URL + 'api/batch/predict', {
        samples: batchSamples,
        targets: targetsToRun,
        mapping: mapping
      });
      setResultsData(res.data.results || []);
      setRunMetadata({ runId, mode: 'Batch', samples: batchSamples.length, targets: targetsToRun, mapping });
      setActivePopup('MODE1');
    } catch (err) {
      alert("Error: " + err.message);
    }
    setProcessing(false);
  };

  const runMode2 = async () => {
    const payloadWvs = { Sample: singleSampleId };
    WAVELENGTHS_ORDER.forEach(nm => payloadWvs[`nm_${nm}`] = parseFloat(wvs[nm]) || 0);
    
    setProcessing(true);
    const runId = 'RUN-' + Math.random().toString(36).substr(2, 6).toUpperCase();
    
    try {
      const res = await axios.post(import.meta.env.BASE_URL + 'api/batch/predict', {
        samples: [payloadWvs],
        targets: [mode2Target],
        mapping: mapping
      });
      setResultsData(res.data.results || []);
      setRunMetadata({ runId, mode: 'Single Nutrient', samples: 1, targets: [mode2Target], mapping });
      setActivePopup('MODE2');
    } catch (err) {
      alert("Error: " + err.message);
    }
    setProcessing(false);
  };

  const runMode3 = async () => {
    const payloadWvs = { Sample: singleSampleId };
    WAVELENGTHS_ORDER.forEach(nm => payloadWvs[`nm_${nm}`] = parseFloat(wvs[nm]) || 0);
    
    setProcessing(true);
    const runId = 'RUN-' + Math.random().toString(36).substr(2, 6).toUpperCase();
    
    // Only run the selected targets from the table
    const targetsToRun = TARGETS.filter(t => selectedTargets[t]);
    if (targetsToRun.length === 0) return alert("Select at least one nutrient.");

    try {
      const res = await axios.post(import.meta.env.BASE_URL + 'api/batch/predict', {
        samples: [payloadWvs],
        targets: targetsToRun,
        mapping: mapping
      });
      setResultsData(res.data.results || []);
      setRunMetadata({ runId, mode: 'Single Sample - All Nutrients', samples: 1, targets: targetsToRun, mapping });
      setActivePopup('MODE3');
    } catch (err) {
      alert("Error: " + err.message);
    }
    setProcessing(false);
  };

  // -------------------------------------------------------------
  // RENDER HELPERS
  // -------------------------------------------------------------

  const WavelengthGrid = () => (
    <div style={{background: 'white', padding: '24px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: '24px'}}>
      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '16px'}}>
        <h3 style={{margin: 0, fontSize: '18px'}}>Wavelength Inputs (nm)</h3>
        <button onClick={loadDemoWavelengths} style={{background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold'}}>Load Demo Values</button>
      </div>
      <div style={{marginBottom: '16px'}}>
        <label style={{fontSize: '14px', fontWeight: 'bold', marginRight: '12px'}}>Sample ID:</label>
        <input value={singleSampleId} onChange={e => setSingleSampleId(e.target.value)} style={{padding: '8px', border: '1px solid #cbd5e1', borderRadius: '6px'}}/>
      </div>
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '12px'}}>
        {WAVELENGTHS_ORDER.map(nm => (
          <div key={nm} style={{display: 'flex', flexDirection: 'column'}}>
            <label style={{fontSize: '11px', color: '#64748b'}}>nm_{nm}</label>
            <input type="number" value={wvs[nm]} onChange={e => setWvs({...wvs, [nm]: e.target.value})} style={{padding: '6px', border: '1px solid #cbd5e1', borderRadius: '4px'}}/>
          </div>
        ))}
      </div>
    </div>
  );

  const ConfigurationTable = ({ allNutrients = true }) => (
    <div style={{background: 'white', padding: '24px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: '24px'}}>
      <h3 style={{margin: 0, fontSize: '18px', marginBottom: '16px'}}>Logic & Calibration Configuration</h3>
      <table style={{width: '100%', borderCollapse: 'collapse'}}>
        <thead>
          <tr style={{background: '#f8fafc', borderBottom: '2px solid #cbd5e1', textAlign: 'left'}}>
            {allNutrients && <th style={{padding: '12px', width: '80px'}}>Select</th>}
            <th style={{padding: '12px'}}>Nutrient</th>
            <th style={{padding: '12px'}}>Prediction Method / Logic</th>
            <th style={{padding: '12px'}}>Calibration</th>
          </tr>
        </thead>
        <tbody>
          {TARGETS.map(t => {
            if (!allNutrients && t !== mode2Target) return null;
            return (
              <tr key={t} style={{borderBottom: '1px solid #e2e8f0', background: (!allNutrients || selectedTargets[t]) ? '#f0fdf4' : 'transparent'}}>
                {allNutrients && (
                  <td style={{padding: '12px', textAlign: 'center'}}>
                    <input type="checkbox" checked={!!selectedTargets[t]} onChange={() => setSelectedTargets(p => ({...p, [t]: !p[t]}))} style={{width: '18px', height: '18px'}} />
                  </td>
                )}
                <td style={{padding: '12px', fontWeight: 'bold'}}>{t}</td>
                <td style={{padding: '12px'}}>
                  <select 
                    value={mapping[t]?.method_id || ''} 
                    onChange={(e) => handleChangeMapping(t, 'method_id', e.target.value)}
                    style={{padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', width: '100%'}}
                  >
                    <optgroup label="Machine Learning">
                      <option value={`${t}_model.pkl`}>ML Model ({t}_model.pkl)</option>
                    </optgroup>
                    <optgroup label="Mathematical Logics">
                      {logics.map(l => (
                        <option key={l.id} value={l.id}>{l.id} - {l.name}</option>
                      ))}
                    </optgroup>
                  </select>
                </td>
                <td style={{padding: '12px'}}>
                  <select 
                    value={mapping[t]?.calibration_required ? 'true' : 'false'}
                    onChange={(e) => handleChangeMapping(t, 'calibration_required', e.target.value === 'true')}
                    style={{padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1'}}
                    disabled={mapping[t]?.method_type === 'ml'}
                  >
                    <option value="true">Required</option>
                    <option value="false">Not Required</option>
                  </select>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  );

  if (loading) return <div style={{padding: '40px', textAlign: 'center'}}>Initializing System...</div>;

  // -------------------------------------------------------------
  // MAIN RENDER
  // -------------------------------------------------------------
  return (
    <div style={{minHeight: '100vh', background: '#f1f5f9'}}>
      <header style={{background: 'white', padding: '16px 32px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', display: 'flex', alignItems: 'center', gap: '16px', position: 'sticky', top: 0, zIndex: 10}}>
        <Activity size={28} color="var(--accent)" />
        <h1 style={{margin: 0, fontSize: '20px'}}>Soil Analysis System</h1>
        {mode && (
          <button onClick={() => setMode(null)} style={{marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px', background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', fontWeight: 'bold'}}>
            <ArrowLeft size={18}/> Return to Mode Selection
          </button>
        )}
      </header>

      <div style={{maxWidth: '1200px', margin: '0 auto', padding: '32px'}}>
        
        {/* MODE SELECTION SCREEN */}
        {!mode && (
          <div>
            <h2 style={{textAlign: 'center', fontSize: '28px', color: '#1e293b', marginBottom: '12px'}}>Select Execution Mode</h2>
            <p style={{textAlign: 'center', color: '#64748b', marginBottom: '40px'}}>Choose the appropriate workflow for your data.</p>
            
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px'}}>
              {/* Card 1 */}
              <div onClick={() => setMode('MODE1')} style={{background: 'white', padding: '32px', borderRadius: '16px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', cursor: 'pointer', border: '2px solid transparent', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', transition: 'border 0.2s'}}>
                <div style={{background: '#e0f2fe', padding: '16px', borderRadius: '50%'}}><Layers size={32} color="#0284c7"/></div>
                <h3 style={{margin: 0, fontSize: '20px'}}>Multiple Samples</h3>
                <p style={{textAlign: 'center', color: '#64748b', fontSize: '14px', lineHeight: '1.5'}}>Upload a CSV/XLSX file with multiple samples. Apply logics to some or all nutrients across the entire batch.</p>
                <div style={{background: '#f1f5f9', padding: '8px 16px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold', color: '#475569', marginTop: 'auto'}}>Batch Workflow</div>
              </div>

              {/* Card 2 */}
              <div onClick={() => setMode('MODE2')} style={{background: 'white', padding: '32px', borderRadius: '16px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', cursor: 'pointer', border: '2px solid transparent', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', transition: 'border 0.2s'}}>
                <div style={{background: '#fef08a', padding: '16px', borderRadius: '50%'}}><Target size={32} color="#ca8a04"/></div>
                <h3 style={{margin: 0, fontSize: '20px'}}>Single Nutrient</h3>
                <p style={{textAlign: 'center', color: '#64748b', fontSize: '14px', lineHeight: '1.5'}}>Enter one sample's wavelengths manually. Focus entirely on predicting one specific nutrient with deep trace details.</p>
                <div style={{background: '#f1f5f9', padding: '8px 16px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold', color: '#475569', marginTop: 'auto'}}>Targeted Workflow</div>
              </div>

              {/* Card 3 */}
              <div onClick={() => setMode('MODE3')} style={{background: 'white', padding: '32px', borderRadius: '16px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', cursor: 'pointer', border: '2px solid transparent', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', transition: 'border 0.2s'}}>
                <div style={{background: '#dcfce7', padding: '16px', borderRadius: '50%'}}><Activity size={32} color="#16a34a"/></div>
                <h3 style={{margin: 0, fontSize: '20px'}}>Single Sample / All 12</h3>
                <p style={{textAlign: 'center', color: '#64748b', fontSize: '14px', lineHeight: '1.5'}}>Enter one sample's wavelengths. Automatically execute and graph all 12 nutrients simultaneously.</p>
                <div style={{background: '#f1f5f9', padding: '8px 16px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold', color: '#475569', marginTop: 'auto'}}>Comprehensive Workflow</div>
              </div>
            </div>
          </div>
        )}

        {/* ----------------- MODE 1 ----------------- */}
        {mode === 'MODE1' && (
          <div>
            <h2 style={{fontSize: '24px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px'}}><Layers color="#0284c7"/> Multiple Samples (Batch)</h2>
            
            <div style={{background: 'white', padding: '24px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: '24px'}}>
              <h3 style={{margin: 0, fontSize: '18px', marginBottom: '16px'}}>1. Upload Data</h3>
              <label style={{background: 'var(--accent)', color: 'white', padding: '12px 24px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold', display: 'inline-flex', alignItems: 'center', gap: '8px'}}>
                <Upload size={18} /> Select CSV/XLSX
                <input type="file" accept=".csv" onChange={parseCSV} style={{display: 'none'}} />
              </label>
              {fileInfo && (
                <div style={{marginTop: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: '#16a34a', background: '#f0fdf4', padding: '12px 16px', borderRadius: '8px'}}>
                  <CheckCircle size={18} /> <strong>{fileInfo.name}</strong> loaded: {fileInfo.samples} Samples, {fileInfo.wvs} Wavelength Columns found.
                </div>
              )}
            </div>

            <ConfigurationTable allNutrients={true} />

            <div style={{textAlign: 'right'}}>
              <button onClick={runMode1} disabled={processing} style={{background: 'var(--accent)', color: 'white', padding: '14px 32px', borderRadius: '8px', border: 'none', fontSize: '18px', fontWeight: 'bold', cursor: processing ? 'not-allowed' : 'pointer'}}>
                {processing ? 'Processing...' : 'Run Batch Analysis'}
              </button>
            </div>
          </div>
        )}

        {/* ----------------- MODE 2 ----------------- */}
        {mode === 'MODE2' && (
          <div>
            <h2 style={{fontSize: '24px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px'}}><Target color="#ca8a04"/> Single Nutrient Execution</h2>
            <WavelengthGrid />
            
            <div style={{background: 'white', padding: '24px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: '24px'}}>
              <h3 style={{margin: 0, fontSize: '18px', marginBottom: '16px'}}>Target Nutrient</h3>
              <select value={mode2Target} onChange={e => setMode2Target(e.target.value)} style={{padding: '12px', fontSize: '16px', borderRadius: '8px', width: '200px'}}>
                {TARGETS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>

            <ConfigurationTable allNutrients={false} />

            <div style={{textAlign: 'right'}}>
              <button onClick={runMode2} disabled={processing} style={{background: 'var(--accent)', color: 'white', padding: '14px 32px', borderRadius: '8px', border: 'none', fontSize: '18px', fontWeight: 'bold', cursor: processing ? 'not-allowed' : 'pointer'}}>
                {processing ? 'Processing...' : `Run Analysis for ${mode2Target}`}
              </button>
            </div>
          </div>
        )}

        {/* ----------------- MODE 3 ----------------- */}
        {mode === 'MODE3' && (
          <div>
            <h2 style={{fontSize: '24px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px'}}><Activity color="#16a34a"/> Single Sample / All 12 Nutrients</h2>
            <WavelengthGrid />
            <ConfigurationTable allNutrients={true} />

            <div style={{textAlign: 'right'}}>
              <button onClick={runMode3} disabled={processing} style={{background: 'var(--accent)', color: 'white', padding: '14px 32px', borderRadius: '8px', border: 'none', fontSize: '18px', fontWeight: 'bold', cursor: processing ? 'not-allowed' : 'pointer'}}>
                {processing ? 'Processing...' : 'Execute All 12 Logics'}
              </button>
            </div>
          </div>
        )}

      </div>

      {/* ==============================================================================
          RESULTS POPUPS
      ================================================================================ */}
      {activePopup && (
        <div style={{position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.8)', zIndex: 100, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '24px'}}>
          <div style={{background: '#f8fafc', width: '100%', maxWidth: '1200px', maxHeight: '90vh', borderRadius: '16px', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'}}>
            
            {/* Modal Header */}
            <div style={{background: 'white', padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <div>
                <h2 style={{margin: 0, fontSize: '24px', color: '#0f172a'}}>
                  {activePopup === 'MODE1' && 'Batch Results'}
                  {activePopup === 'MODE2' && 'Single Nutrient Result'}
                  {activePopup === 'MODE3' && 'Single Sample Results'}
                </h2>
                <div style={{display: 'flex', gap: '16px', marginTop: '8px'}}>
                  <span style={{fontSize: '12px', background: '#e2e8f0', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold', color: '#475569'}}>RUN ID: {runMetadata.runId}</span>
                  <span style={{fontSize: '12px', background: '#e2e8f0', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold', color: '#475569'}}>Samples: {runMetadata.samples}</span>
                  <span style={{fontSize: '12px', background: '#e2e8f0', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold', color: '#475569'}}>Targets: {runMetadata.targets?.length}</span>
                </div>
              </div>
              <button onClick={() => setActivePopup(null)} style={{background: '#ef4444', color: 'white', border: 'none', borderRadius: '50%', width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer'}}>
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{padding: '24px', overflowY: 'auto', flex: 1}}>
              
              {/* MODE 1 BODY */}
              {activePopup === 'MODE1' && (
                <div>
                  <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px'}}>
                    <div style={{background: 'white', padding: '16px', borderRadius: '12px', border: '1px solid #cbd5e1'}}>
                      <h3 style={{marginTop: 0, fontSize: '16px', color: '#475569'}}>Actual vs Predicted (Aggregate)</h3>
                      <div style={{height: '250px'}}>
                        <ResponsiveContainer>
                          <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                            <CartesianGrid />
                            <XAxis type="number" dataKey="Actual" name="Actual" />
                            <YAxis type="number" dataKey="Predicted" name="Predicted" />
                            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                            <Scatter data={resultsData.filter(r => r.Actual != null)} fill="var(--accent)" />
                            <ReferenceLine segment={[{x: 0, y: 0}, {x: 100, y: 100}]} stroke="red" strokeDasharray="3 3"/>
                          </ScatterChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    <div style={{background: 'white', padding: '16px', borderRadius: '12px', border: '1px solid #cbd5e1'}}>
                      <h3 style={{marginTop: 0, fontSize: '16px', color: '#475569'}}>Prediction Error Distribution</h3>
                      <div style={{height: '250px'}}>
                        <ResponsiveContainer>
                          <BarChart data={resultsData.filter(r => r.Error != null)}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="Sample" hide />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="Error" fill="#f59e0b" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>

                  <div style={{background: 'white', borderRadius: '12px', border: '1px solid #cbd5e1', overflow: 'hidden'}}>
                    <table style={{width: '100%', borderCollapse: 'collapse'}}>
                      <thead>
                        <tr style={{background: '#f1f5f9', borderBottom: '2px solid #cbd5e1', textAlign: 'left'}}>
                          <th style={{padding: '12px'}}>Sample ID</th>
                          <th style={{padding: '12px'}}>Nutrient</th>
                          <th style={{padding: '12px'}}>Method</th>
                          <th style={{padding: '12px'}}>Predicted</th>
                          <th style={{padding: '12px'}}>Actual</th>
                          <th style={{padding: '12px'}}>Error</th>
                          <th style={{padding: '12px'}}>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {resultsData.map((r, i) => (
                          <tr key={i} style={{borderBottom: '1px solid #e2e8f0'}}>
                            <td style={{padding: '12px'}}>{r.Sample}</td>
                            <td style={{padding: '12px', fontWeight: 'bold'}}>{r.Target}</td>
                            <td style={{padding: '12px'}}>{r.Method}</td>
                            <td style={{padding: '12px', fontWeight: 'bold'}}>{r.Predicted != null ? Number(r.Predicted).toFixed(2) : '-'}</td>
                            <td style={{padding: '12px'}}>{r.Actual != null ? Number(r.Actual).toFixed(2) : '-'}</td>
                            <td style={{padding: '12px'}}>{r.Error != null ? Number(r.Error).toFixed(2) : '-'}</td>
                            <td style={{padding: '12px'}}>
                              <span style={{padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold', background: r.Status?.includes('FAILED') ? '#fecaca' : r.Status === 'HIGH' ? '#fde68a' : r.Status === 'LOW' || r.Status === 'Deficient' ? '#fed7aa' : '#bbf7d0', color: r.Status?.includes('FAILED') ? '#991b1b' : '#1e293b'}}>
                                {r.Status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* MODE 2 BODY */}
              {activePopup === 'MODE2' && resultsData[0] && (
                <div style={{display: 'flex', flexDirection: 'column', gap: '24px'}}>
                  <div style={{display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px'}}>
                    
                    {/* Big Result Card */}
                    <div style={{background: 'white', padding: '32px', borderRadius: '12px', border: '1px solid #cbd5e1', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
                      <h3 style={{margin: '0 0 16px 0', fontSize: '20px', color: '#64748b'}}>{resultsData[0].Target} Prediction</h3>
                      <div style={{fontSize: '64px', fontWeight: 'bold', color: 'var(--accent)', lineHeight: '1'}}>
                        {resultsData[0].Predicted != null ? Number(resultsData[0].Predicted).toFixed(2) : '-'}
                      </div>
                      <div style={{fontSize: '18px', color: '#94a3b8', marginTop: '8px'}}>kg/ha</div>
                      
                      <div style={{marginTop: '24px', padding: '8px 24px', borderRadius: '24px', fontSize: '16px', fontWeight: 'bold', background: resultsData[0].Status?.includes('FAILED') ? '#fecaca' : resultsData[0].Status === 'HIGH' ? '#fde68a' : resultsData[0].Status === 'LOW' || resultsData[0].Status === 'Deficient' ? '#fed7aa' : '#bbf7d0', color: resultsData[0].Status?.includes('FAILED') ? '#991b1b' : '#1e293b'}}>
                        STATUS: {resultsData[0].Status}
                      </div>
                    </div>

                    {/* Trace Details */}
                    <div style={{background: 'white', padding: '24px', borderRadius: '12px', border: '1px solid #cbd5e1'}}>
                      <h3 style={{marginTop: 0, borderBottom: '1px solid #e2e8f0', paddingBottom: '12px'}}>Execution Trace Details</h3>
                      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '14px'}}>
                        <div><strong style={{color: '#64748b', display: 'block'}}>Method Logic ID</strong>{resultsData[0].Method}</div>
                        <div><strong style={{color: '#64748b', display: 'block'}}>Method Type</strong>{resultsData[0].MethodType}</div>
                        <div><strong style={{color: '#64748b', display: 'block'}}>Calibration Status</strong>{resultsData[0].Calibration}</div>
                        <div><strong style={{color: '#64748b', display: 'block'}}>Raw Mathematical Pred</strong>{resultsData[0].Raw_Prediction != null ? Number(resultsData[0].Raw_Prediction).toFixed(4) : '-'}</div>
                        <div><strong style={{color: '#64748b', display: 'block'}}>Min Limit Documented</strong>{resultsData[0].Min_Limit != null ? resultsData[0].Min_Limit : 'None'}</div>
                        <div><strong style={{color: '#64748b', display: 'block'}}>Max Limit Documented</strong>{resultsData[0].Max_Limit != null ? resultsData[0].Max_Limit : 'None'}</div>
                        <div><strong style={{color: '#64748b', display: 'block'}}>Clamp Enforced</strong>{resultsData[0].Clamp_Applied ? 'YES' : 'NO'}</div>
                        <div><strong style={{color: '#64748b', display: 'block'}}>ML Class Branch</strong>{resultsData[0].ML_Class || '-'}</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* MODE 3 BODY */}
              {activePopup === 'MODE3' && (
                <div>
                  <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px'}}>
                    {resultsData.map((r, i) => (
                      <div key={i} style={{background: 'white', padding: '16px', borderRadius: '12px', border: '1px solid #cbd5e1', borderTop: `4px solid ${r.Status === 'Adequate' || r.Status === 'MEDIUM' ? '#22c55e' : r.Status?.includes('FAILED') ? '#ef4444' : '#eab308'}`}}>
                        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px'}}>
                          <span style={{fontSize: '20px', fontWeight: 'bold'}}>{r.Target}</span>
                          <span style={{fontSize: '12px', color: '#64748b'}}>{r.Method}</span>
                        </div>
                        <div style={{fontSize: '28px', fontWeight: 'bold', color: '#0f172a'}}>
                          {r.Predicted != null ? Number(r.Predicted).toFixed(2) : 'ERR'}
                        </div>
                        <div style={{fontSize: '13px', fontWeight: 'bold', marginTop: '8px', color: '#475569'}}>{r.Status}</div>
                      </div>
                    ))}
                  </div>

                  <div style={{background: 'white', borderRadius: '12px', border: '1px solid #cbd5e1', overflow: 'hidden'}}>
                    <table style={{width: '100%', borderCollapse: 'collapse'}}>
                      <thead>
                        <tr style={{background: '#f1f5f9', borderBottom: '2px solid #cbd5e1', textAlign: 'left'}}>
                          <th style={{padding: '12px'}}>Nutrient</th>
                          <th style={{padding: '12px'}}>Method</th>
                          <th style={{padding: '12px'}}>Calibration</th>
                          <th style={{padding: '12px'}}>Prediction</th>
                          <th style={{padding: '12px'}}>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {resultsData.map((r, i) => (
                          <tr key={i} style={{borderBottom: '1px solid #e2e8f0'}}>
                            <td style={{padding: '12px', fontWeight: 'bold'}}>{r.Target}</td>
                            <td style={{padding: '12px'}}>{r.Method}</td>
                            <td style={{padding: '12px'}}>{r.Calibration}</td>
                            <td style={{padding: '12px', fontWeight: 'bold'}}>{r.Predicted != null ? Number(r.Predicted).toFixed(2) : '-'}</td>
                            <td style={{padding: '12px'}}>
                              <span style={{padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold', background: r.Status?.includes('FAILED') ? '#fecaca' : r.Status === 'HIGH' ? '#fde68a' : r.Status === 'LOW' || r.Status === 'Deficient' ? '#fed7aa' : '#bbf7d0', color: r.Status?.includes('FAILED') ? '#991b1b' : '#1e293b'}}>
                                {r.Status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default MainAnalysis;
