import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTheme } from '../context/ThemeContext';
import { ALL_TARGETS } from '../utils/fileParser';

const BASE = 'http://127.0.0.1:5000';

export default function CalibrationManagement() {
  const { colors } = useTheme();
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [selectedNutrient, setSelectedNutrient] = useState(null);
  const [msg, setMsg] = useState('');

  const refresh = () => {
    axios.get(`${BASE}/api/calibration`).then(r => setStatus(r.data)).catch(e => {
      setStatus({ status: 'NOT_FOUND', message: e.response?.data?.message || 'No calibration file uploaded.' });
    });
  };

  useEffect(() => { refresh(); }, []);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true); 
    setMsg('');
    const fd = new FormData();
    fd.append('file', file);
    try {
      await axios.post(`${BASE}/api/calibration/upload`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setMsg('Calibration uploaded successfully!');
      refresh();
    } catch(err) {
      setMsg('Error: ' + (err.response?.data?.error || err.message));
    } finally {
      setUploading(false);
    }
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

  const nutrientData = selectedNutrient && status?.data?.[selectedNutrient];

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 800, color: colors.textPrimary, marginBottom: 20 }}>📁 Calibration Management</h2>

      {msg && (
        <div style={{ 
          background: msg.startsWith('Error') ? '#ef444415' : '#16a34a15', 
          color: msg.startsWith('Error') ? '#ef4444' : '#16a34a', 
          border: `1px solid ${msg.startsWith('Error') ? '#ef444440' : '#16a34a40'}`,
          borderRadius: 8, 
          padding: 14, 
          marginBottom: 20,
          fontSize: 13,
          fontWeight: 600
        }}>
          {msg}
        </div>
      )}

      {/* Status Banner */}
      <div style={{ ...cardStyle, border: `1.5px solid ${status?.status === 'VALID' ? '#16a34a' : '#dc2626'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h3 style={{ color: status?.status === 'VALID' ? '#16a34a' : '#dc2626', fontSize: 18, margin: 0, marginBottom: 4 }}>
              {status?.status === 'VALID' ? '✓ Calibration File Active' : '✗ Calibration File Missing'}
            </h3>
            <div style={{ color: colors.textMuted, fontSize: 13 }}>
              Source: <strong style={{ color: colors.textPrimary }}>{status?.filename || 'None'}</strong> &nbsp;|&nbsp; Available: <strong style={{ color: colors.accent }}>{status?.nutrients_available || 0}/12 nutrients</strong>
            </div>
          </div>
          <div>
            <label style={{ ...btnStyle(colors.accent), display: 'inline-block', cursor: 'pointer' }}>
              {uploading ? 'Uploading...' : '⬆ Upload Calibration JSON'}
              <input type="file" accept=".json" onChange={handleUpload} style={{ display: 'none' }} />
            </label>
          </div>
        </div>
      </div>

      {/* Nutrients Grid */}
      {status?.data && (
        <div style={cardStyle}>
          <h3 style={{ color: colors.accent, fontSize: 18, fontWeight: 700, marginBottom: 14 }}>Nutrient Sections Status</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 12 }}>
            {ALL_TARGETS.map(t => {
              const has = status.nutrients?.includes(t);
              const isSelected = selectedNutrient === t;
              return (
                <div 
                  key={t} 
                  onClick={() => setSelectedNutrient(isSelected ? null : t)}
                  style={{ 
                    background: isSelected ? (has ? '#16a34a15' : '#dc262615') : colors.inputBg,
                    border: `1.5px solid ${isSelected ? (has ? '#16a34a' : '#dc2626') : colors.cardBorder}`,
                    borderRadius: 10, 
                    padding: 16, 
                    cursor: 'pointer', 
                    textAlign: 'center',
                    transition: 'all 0.15s' 
                  }}
                >
                  <div style={{ fontSize: 22, marginBottom: 4 }}>{has ? '✓' : '✗'}</div>
                  <div style={{ fontWeight: 800, fontSize: 16, color: has ? '#16a34a' : '#dc2626' }}>{t}</div>
                  <div style={{ color: colors.textMuted, fontSize: 11, marginTop: 4 }}>{has ? 'Valid Data' : 'Missing'}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Nutrient Data Preview */}
      {selectedNutrient && nutrientData && (
        <div style={cardStyle}>
          <h3 style={{ color: colors.accent, fontSize: 18, fontWeight: 700, marginBottom: 16 }}>
            {selectedNutrient} — Calibration Values Preview
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginBottom: 20 }}>
            {[
              ['value_min', nutrientData.value_min],
              ['value_mid', nutrientData.value_mid],
              ['value_max', nutrientData.value_max],
              ['indices', JSON.stringify(nutrientData.indices || [])],
              ['vals', JSON.stringify(nutrientData.vals || [])],
            ].map(([k, v]) => (
              <div key={k} style={{ background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: 12 }}>
                <div style={{ color: colors.textMuted, fontSize: 11, marginBottom: 4 }}>{k}</div>
                <div style={{ color: colors.textPrimary, fontFamily: 'monospace', fontSize: 13, wordBreak: 'break-all', fontWeight: 600 }}>
                  {String(v)}
                </div>
              </div>
            ))}
          </div>

          {['min', 'mid', 'max'].map(k => {
            const arr = nutrientData[k] || [];
            if (!arr.length) return null;
            return (
              <div key={k} style={{ marginBottom: 14 }}>
                <div style={{ color: colors.textSecondary, fontSize: 12, fontWeight: 600, marginBottom: 6 }}>
                  {k} reference spectrum ({arr.length} wavelength values)
                </div>
                <div style={{ background: colors.inputBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: 12, fontFamily: 'monospace', fontSize: 11, color: colors.textMuted, overflowX: 'auto', whiteSpace: 'nowrap' }}>
                  {arr.slice(0, 12).map(v => typeof v === 'number' ? v.toFixed(2) : v).join('   ')}
                  {arr.length > 12 && <span style={{ color: colors.accent }}>  ...+{arr.length - 12} more</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedNutrient && !nutrientData && (
        <div style={{ ...cardStyle, color: '#dc2626', fontWeight: 600 }}>
          No calibration section found for nutrient {selectedNutrient} in uploaded JSON file.
        </div>
      )}
    </div>
  );
}
