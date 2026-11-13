import React, { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';

export default function TrainModels() {
  const { colors } = useTheme();
  const [trainFile, setTrainFile] = useState(null);
  const [testFile, setTestFile] = useState(null);
  const [status, setStatus] = useState('');
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [testResults, setTestResults] = useState([]);
  const [reportUrl, setReportUrl] = useState('');

  useEffect(() => {
    fetch('/api/models')
      .then(res => res.json())
      .then(data => {
        setModels(data);
        if (data.length > 0) setSelectedModel(data[0].id);
      })
      .catch(err => console.error(err));
  }, []);

  const handleTrain = async () => {
    if (!trainFile) {
      alert('Please select an Excel file for training.');
      return;
    }
    
    const formData = new FormData();
    formData.append('file', trainFile);
    if (selectedModel) formData.append('model_name', selectedModel);
    
    setStatus('Training model(s)... This might take a minute...');
    setTestResults([]);
    setReportUrl('');
    try {
      const res = await fetch('/api/models/train', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setStatus(data.message || 'Model successfully retrained!');
      } else {
        setStatus(`Error: ${data.error || 'Failed to train'}`);
      }
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    }
  };

  const handleTest = async () => {
    if (!testFile) {
      alert('Please select an Excel file for testing.');
      return;
    }
    
    const formData = new FormData();
    formData.append('file', testFile);
    if (selectedModel) formData.append('model_name', selectedModel);
    
    setStatus('Testing model...');
    setTestResults([]);
    setReportUrl('');
    try {
      const res = await fetch('/api/models/test', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setStatus('Testing complete!');
        setTestResults(data.results);
        if (data.report_url) {
          setReportUrl(data.report_url);
        }
      } else {
        setStatus(`Error: ${data.error || 'Failed to test'}`);
      }
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '40px 20px', background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 12 }}>
      <h2 style={{ fontSize: 24, fontWeight: 700, color: colors.textPrimary, marginBottom: 12 }}>Train & Test Models</h2>
      <p style={{ color: colors.textSecondary, marginBottom: 24 }}>
        Select a specific model architecture to retrain on your dataset or test against your dataset to view actual vs predicted results.
      </p>
      
      <div style={{ marginBottom: 24 }}>
        <label style={{ display: 'block', marginBottom: 8, color: colors.textPrimary, fontWeight: 600 }}>Select Model Architecture:</label>
        <select 
          value={selectedModel} 
          onChange={e => setSelectedModel(e.target.value)}
          style={{ width: '100%', padding: 12, borderRadius: 8, border: `1px solid ${colors.cardBorder}`, background: colors.bg, color: colors.textPrimary, fontSize: 14 }}
        >
          <option value="ALL">★ Train All Models at Once (All 70+ Architectures)</option>
          <optgroup label="Select Specific Architecture">
            {models.map(m => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </optgroup>
        </select>
      </div>

      <div style={{ display: 'flex', gap: 24, marginBottom: 24, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 280, padding: 20, border: `1px dashed ${colors.cardBorder}`, borderRadius: 8, background: colors.bg }}>
          <h3 style={{ fontSize: 18, color: colors.textPrimary, marginBottom: 8 }}>1. Train Model(s)</h3>
          <p style={{ fontSize: 13, color: colors.textSecondary, marginBottom: 14 }}>
            {selectedModel === 'ALL' 
              ? 'Upload your dataset to train all 70+ model architectures simultaneously.'
              : `Upload your dataset to train the selected model (${selectedModel}).`}
          </p>
          <input 
            type="file" 
            accept=".xlsx,.xls" 
            onChange={e => setTrainFile(e.target.files[0])}
            style={{ color: colors.textPrimary, marginBottom: 16, display: 'block', fontSize: 13 }}
          />
          <button 
            onClick={handleTrain}
            style={{ 
              background: selectedModel === 'ALL' ? '#8b5cf6' : '#f59e0b', 
              color: '#fff', 
              border: 'none', 
              padding: '10px 22px', 
              borderRadius: 8, 
              fontWeight: 600, 
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8
            }}
          >
            {selectedModel === 'ALL' ? '⚡ Train All Models at Once' : 'Upload & Train Selected Model'}
          </button>
        </div>

        <div style={{ flex: 1, minWidth: 280, padding: 20, border: `1px dashed ${colors.cardBorder}`, borderRadius: 8, background: colors.bg }}>
          <h3 style={{ fontSize: 18, color: colors.textPrimary, marginBottom: 8 }}>2. Test Model</h3>
          <p style={{ fontSize: 13, color: colors.textSecondary, marginBottom: 14 }}>
            Upload a validation file to test predictions, compare actuals vs predicted, and download an Excel report.
          </p>
          <input 
            type="file" 
            accept=".xlsx,.xls" 
            onChange={e => setTestFile(e.target.files[0])}
            style={{ color: colors.textPrimary, marginBottom: 16, display: 'block', fontSize: 13 }}
          />
          <button 
            onClick={handleTest}
            disabled={selectedModel === 'ALL'}
            style={{ 
              background: selectedModel === 'ALL' ? '#9ca3af' : '#3b82f6', 
              color: '#fff', 
              border: 'none', 
              padding: '10px 22px', 
              borderRadius: 8, 
              fontWeight: 600, 
              cursor: selectedModel === 'ALL' ? 'not-allowed' : 'pointer' 
            }}
          >
            Upload & Test
          </button>
          {selectedModel === 'ALL' && (
            <div style={{ fontSize: 11, color: '#ef4444', marginTop: 6 }}>
              Select a specific model above to run testing.
            </div>
          )}
        </div>
      </div>
      
      {status && (
        <div style={{ marginBottom: 24, padding: 16, background: status.includes('Error') ? '#fee2e2' : '#dcfce7', color: status.includes('Error') ? '#991b1b' : '#166534', borderRadius: 8, fontWeight: 500 }}>
          {status}
        </div>
      )}

      {reportUrl && (
        <div style={{ marginBottom: 24, padding: 16, background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 8 }}>
          <h4 style={{ color: '#0369a1', margin: '0 0 8px 0' }}>Excel Report Ready!</h4>
          <a href={reportUrl} download style={{ display: 'inline-block', background: '#0284c7', color: 'white', padding: '8px 16px', borderRadius: 4, textDecoration: 'none', fontWeight: 500 }}>
            📥 Download Excel Report with Scatter Charts
          </a>
        </div>
      )}

      {testResults.length > 0 && (
        <div>
          <h3 style={{ fontSize: 18, color: colors.textPrimary, marginBottom: 12 }}>Test Results (Actual vs Predicted)</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: colors.textPrimary }}>
              <thead>
                <tr style={{ background: colors.bg, borderBottom: `2px solid ${colors.cardBorder}` }}>
                  <th style={{ padding: 12 }}>Sample ID</th>
                  <th style={{ padding: 12 }}>Nutrient</th>
                  <th style={{ padding: 12 }}>Actual</th>
                  <th style={{ padding: 12 }}>Predicted</th>
                  <th style={{ padding: 12 }}>Error</th>
                </tr>
              </thead>
              <tbody>
                {testResults.map((r, i) => (
                  <tr key={i} style={{ borderBottom: `1px solid ${colors.cardBorder}` }}>
                    <td style={{ padding: 12 }}>{r.sample_id}</td>
                    <td style={{ padding: 12 }}>{r.nutrient}</td>
                    <td style={{ padding: 12 }}>{r.actual !== null ? r.actual.toFixed(2) : 'N/A'}</td>
                    <td style={{ padding: 12 }}>{r.predicted !== null ? r.predicted.toFixed(2) : 'N/A'}</td>
                    <td style={{ padding: 12, color: Math.abs(r.error) > 5 ? '#ef4444' : (Math.abs(r.error) < 1 ? '#10b981' : 'inherit') }}>
                      {r.error !== null ? r.error.toFixed(2) : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
