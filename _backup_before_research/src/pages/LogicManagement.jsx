import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTheme } from '../context/ThemeContext';
import { Plus, Edit2, Save, X, FileCode } from 'lucide-react';

const BASE = 'http://127.0.0.1:5000';

export default function LogicManagement() {
  const { colors } = useTheme();
  const [logics, setLogics] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  // Editor state
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState(null);
  const [editCode, setEditCode] = useState("");

  const fetchLogics = () => {
    setLoading(true);
    axios.get(`${BASE}/api/logics`)
      .then(r => { setLogics(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchLogics();
  }, []);

  const handleEdit = (logic) => {
    axios.get(`${BASE}/api/logics/${logic.id}`).then(res => {
      setEditForm({
        ...res.data.definition,
        target: res.data.definition.target || '',
        type: res.data.definition.type || 'Mathematical',
        formula: res.data.definition.formula || '',
        calibration_source: res.data.definition.calibration_source || '',
        limits: res.data.definition.limits || '',
        unit: res.data.definition.unit || '',
        version: res.data.definition.version || '1.0',
        review_status: res.data.definition.review_status || 'Draft',
        features: Array.isArray(res.data.definition.features) ? res.data.definition.features.join(', ') : (res.data.definition.features || '')
      });
      setEditCode(res.data.implementation || "");
      setIsEditing(true);
    }).catch(e => {
        setEditForm({...logic, target: '', type: 'Mathematical', formula: '', calibration_source: '', limits: '', unit: '', version: '1.0', review_status: 'Draft', features: ''});
        setEditCode("");
        setIsEditing(true);
    });
  };

  const handleAddNew = () => {
    setEditForm({
      id: '',
      name: '',
      target: '',
      type: 'Mathematical',
      features: '',
      formula: '',
      calibration_required: false,
      calibration_source: '',
      limits: '',
      unit: '',
      version: '1.0',
      review_status: 'Draft'
    });
    setEditCode("");
    setIsEditing(true);
  };

  const handleSave = () => {
    if (!editForm.id) return alert("Logic ID is required");
    const payload = {
      id: editForm.id,
      definition: {
        ...editForm,
        features: typeof editForm.features === 'string' ? editForm.features.split(',').map(s=>s.trim()).filter(Boolean) : editForm.features
      },
      implementation: editCode
    };
    axios.post(`${BASE}/api/logics`, payload).then(() => {
      setIsEditing(false);
      fetchLogics();
    }).catch(err => alert("Error saving logic: " + err.message));
  };

  const filtered = logics.filter(l =>
    l.id?.toLowerCase().includes(search.toLowerCase()) ||
    l.name?.toLowerCase().includes(search.toLowerCase()) ||
    l.target?.toLowerCase().includes(search.toLowerCase())
  );
  
  const implemented = filtered.filter(l => l.status === 'Implemented');
  const notImplemented = filtered.filter(l => l.status !== 'Implemented');

  const cardStyle = { background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 12, padding: 24, marginBottom: 20 };
  const inputStyle = { background: colors.inputBg, color: colors.inputColor, border: `1px solid ${colors.inputBorder}`, borderRadius: 8, padding: '8px 14px', fontSize: 13, width: '100%' };
  const labelStyle = { display: 'block', fontSize: 12, fontWeight: 600, color: colors.textSecondary, marginBottom: 6 };

  if (isEditing && editForm) {
    return (
      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontSize: 20, fontWeight: 800, color: colors.accent, margin: 0 }}>
            {logics.find(l => l.id === editForm.id) ? `Edit Logic: ${editForm.id}` : 'Add New Logic'}
          </h2>
          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={() => setIsEditing(false)} style={{ background: colors.inputBg, color: colors.textPrimary, border: `1px solid ${colors.cardBorder}`, padding: '8px 16px', borderRadius: 8, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
              <X size={16} /> Cancel
            </button>
            <button onClick={handleSave} style={{ background: '#16a34a', color: 'white', border: 'none', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
              <Save size={16} /> Save Logic
            </button>
          </div>
        </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
            
            <div><label style={labelStyle}>Logic ID</label><input style={inputStyle} value={editForm.id} onChange={e => setEditForm({...editForm, id: e.target.value})} disabled={logics.some(l => l.id === editForm.id)} placeholder="e.g. M27" /></div>
            <div><label style={labelStyle}>Logic Name</label><input style={inputStyle} value={editForm.name} onChange={e => setEditForm({...editForm, name: e.target.value})} placeholder="e.g. Advanced Interpolation" /></div>
            
            <div><label style={labelStyle}>Target Nutrient(s)</label><input style={inputStyle} value={editForm.target} onChange={e => setEditForm({...editForm, target: e.target.value})} placeholder="e.g. OC, N, P, All 12" /></div>
            <div>
              <label style={labelStyle}>Method Type</label>
              <select style={inputStyle} value={editForm.type} onChange={e => setEditForm({...editForm, type: e.target.value})}>
                <option value="Mathematical">Mathematical</option>
                <option value="Rule">Rule</option>
                <option value="Python">Python</option>
              </select>
            </div>
            
            <div><label style={labelStyle}>Required Wavelengths</label><input style={inputStyle} value={editForm.features} onChange={e => setEditForm({...editForm, features: e.target.value})} placeholder="e.g. nm_410, nm_435 (comma separated)" /></div>
            <div><label style={labelStyle}>Required IPS</label><input style={inputStyle} value={editForm.required_ips} onChange={e => setEditForm({...editForm, required_ips: e.target.value})} placeholder="e.g. None, ip1, ip2, ip3" /></div>
            
            <div><label style={labelStyle}>Output Unit</label><input style={inputStyle} value={editForm.unit} onChange={e => setEditForm({...editForm, unit: e.target.value})} placeholder="e.g. %, ppm, Kg/ha" /></div>
            <div><label style={labelStyle}>Lower & Upper Boundary</label><input style={inputStyle} value={editForm.limits} onChange={e => setEditForm({...editForm, limits: e.target.value})} placeholder="e.g. [0.1, 1.5] or nutrient-specific bounds" /></div>
            
            <div style={{ display: 'flex', gap: 10 }}>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>Version</label>
                <input style={inputStyle} value={editForm.version} onChange={e => setEditForm({...editForm, version: e.target.value})} />
              </div>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>Verification Status</label>
                <select style={inputStyle} value={editForm.verification_status} onChange={e => setEditForm({...editForm, verification_status: e.target.value})}>
                    <option value="INCOMPLETE">INCOMPLETE</option>
                    <option value="VERIFIED">VERIFIED</option>
                </select>
              </div>
            </div>
          </div>
          
          <div style={{ marginTop: 20 }}>
             <label style={labelStyle}>Formula / Calculation Steps</label>
             <textarea style={{...inputStyle, minHeight: 80, resize: 'vertical'}} value={editForm.formula} onChange={e => setEditForm({...editForm, formula: e.target.value})} placeholder="Describe the mathematical formula or calculation steps..." />
          </div>

          <div style={{ marginTop: 20, background: colors.name === 'dark' ? '#1e293b' : '#f8fafc', padding: 16, borderRadius: 8, border: `1px solid ${colors.cardBorder}` }}>
             <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontWeight: 600, color: colors.textPrimary, marginBottom: editForm.calibration_required ? 12 : 0 }}>
                <input type="checkbox" checked={editForm.calibration_required} onChange={e => setEditForm({...editForm, calibration_required: e.target.checked})} style={{ accentColor: colors.accent, width: 16, height: 16 }} />
                Calibration Required
             </label>
             {editForm.calibration_required && (
                 <div>
                     <label style={labelStyle}>Calibration Data / Points</label>
                     <input style={inputStyle} value={editForm.calibration_source} onChange={e => setEditForm({...editForm, calibration_source: e.target.value})} placeholder="e.g. calibration.json['OC'] or specific vectors" />
                 </div>
             )}
          </div>
          
          <div style={{ marginTop: 20 }}>
             <label style={{...labelStyle, display: 'flex', alignItems: 'center', gap: 6}}><FileCode size={14}/> Python Implementation (predict function)</label>
             <textarea 
                style={{...inputStyle, fontFamily: 'monospace', fontSize: 13, minHeight: 250, resize: 'vertical', background: '#0f172a', color: '#e2e8f0', border: '1px solid #334155'}} 
                value={editCode} 
                onChange={e => setEditCode(e.target.value)} 
                placeholder="def predict(s, d):&#10;    return 0.0" 
             />
             <div style={{fontSize: 11, color: colors.textMuted, marginTop: 4}}>File will be saved to: logics/implementations/{editForm.id}.py</div>
          </div>

        </div>
      );
    }

  const renderTable = (list, title) => (
    <div style={{ marginBottom: 30 }}>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: colors.textPrimary, marginBottom: 12, borderBottom: `1px solid ${colors.tableBorder}`, paddingBottom: 8 }}>{title} ({list.length})</h3>
        <div style={{ overflowX: 'auto', border: `1px solid ${colors.cardBorder}`, borderRadius: 12, background: colors.cardBg }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
                <tr style={{ background: colors.tableHeaderBg, color: colors.textMuted, borderBottom: `1px solid ${colors.tableBorder}` }}>
                {['Logic ID', 'Name', 'Target', 'Type', 'Calibration', 'Status', 'Actions'].map(h => (
                    <th key={h} style={{ padding: '12px 14px', textAlign: 'left', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
                </tr>
            </thead>
            <tbody>
                {list.map(l => {
                const isImpl = l.status === 'Implemented';
                const isExpanded = expanded === l.id;
                return (
                    <React.Fragment key={l.id}>
                    <tr style={{ borderBottom: `1px solid ${colors.tableBorder}`, background: isExpanded ? colors.navLinkActiveBg : 'transparent' }}>
                        <td style={{ padding: '12px 14px', fontWeight: 800, fontFamily: 'monospace', color: colors.accent, cursor: 'pointer' }} onClick={() => setExpanded(isExpanded ? null : l.id)}>{l.id}</td>
                        <td style={{ padding: '12px 14px', color: colors.textPrimary, fontWeight: 500 }}>{l.name || '-'}</td>
                        <td style={{ padding: '12px 14px', color: colors.textSecondary }}>{l.target || 'All'}</td>
                        <td style={{ padding: '12px 14px', color: colors.textSecondary }}>{l.type || 'Mathematical'}</td>
                        <td style={{ padding: '12px 14px', color: l.calibration_required ? '#16a34a' : colors.textMuted }}>{l.calibration_required ? 'Req' : 'No'}</td>
                        <td style={{ padding: '12px 14px' }}>
                            <span style={{ background: isImpl ? '#16a34a20' : '#dc262620', color: isImpl ? '#16a34a' : '#dc2626', borderRadius: 4, padding: '4px 8px', fontSize: 11, fontWeight: 700 }}>
                                {isImpl ? '✓ Implemented' : '✗ Unimplemented'}
                            </span>
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                            <button onClick={() => handleEdit(l)} style={{ background: 'transparent', border: 'none', color: colors.accent, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, fontWeight: 600 }}>
                                <Edit2 size={14} /> Edit
                            </button>
                        </td>
                    </tr>
                    {isExpanded && (
                        <tr style={{ background: colors.inputBg }}>
                        <td colSpan={7} style={{ padding: '16px 20px' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginBottom: 12 }}>
                            {[
                                ['Logic ID', l.id],
                                ['Name', l.name || 'N/A'],
                                ['Target Nutrient(s)', l.target || 'N/A'],
                                ['Type', l.type || 'Mathematical'],
                                ['Output Unit', l.unit || 'N/A'],
                                ['Required IPS', (l.required_ips && l.required_ips.length > 0) ? l.required_ips.join(', ') : 'None'],
                                ['Limits / Bounds', l.limits || 'N/A'],
                                ['Version', l.version || '1.0'],
                                ['Verification Status', l.verification_status || 'Draft'],
                                ['Impl File', `logics/implementations/${l.id}.py`],
                                ['Calibration Requirement', l.calibration_required ? 'Required' : 'Not Required'],
                                ['Calibration Source', l.calibration_source || 'N/A']
                            ].map(([k, v]) => (
                                <div key={k} style={{ background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: 12 }}>
                                <div style={{ color: colors.textMuted, fontSize: 11, marginBottom: 4 }}>{k}</div>
                                <div style={{ color: colors.textPrimary, fontWeight: 600, fontSize: 12, wordBreak: 'break-all' }}>{v}</div>
                                </div>
                            ))}
                            </div>
                            
                            <div style={{ background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: 12, marginBottom: 12 }}>
                                <div style={{ color: colors.textMuted, fontSize: 11, fontWeight: 600, marginBottom: 6 }}>Required Wavelengths / Inputs</div>
                                <div style={{ fontFamily: 'monospace', fontSize: 12, color: colors.textSecondary }}>
                                    {l.features && l.features.length > 0 ? (Array.isArray(l.features) ? l.features.join(', ') : String(l.features)) : 'All 21 wavelengths'}
                                </div>
                            </div>

                            <div style={{ background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 8, padding: 12 }}>
                                <div style={{ color: colors.textMuted, fontSize: 11, fontWeight: 600, marginBottom: 6 }}>How This Logic Is Calculated</div>
                                <div style={{ fontSize: 13, color: colors.textPrimary, whiteSpace: 'pre-wrap' }}>
                                    {l.formula || 'No formula documented.'}
                                </div>
                            </div>
                        </td>
                        </tr>
                    )}
                    </React.Fragment>
                );
                })}
            </tbody>
            </table>
        </div>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: colors.textPrimary, margin: 0 }}>📚 NON-ML / Calculation Logics</h2>
          <button onClick={handleAddNew} style={{ background: colors.accent, color: '#0f172a', border: 'none', padding: '10px 18px', borderRadius: 8, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700 }}>
             <Plus size={18} /> Add New Logic
          </button>
      </div>

      <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          style={{...inputStyle, maxWidth: 300}}
          placeholder="Filter by Logic ID, Name, Target..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <span style={{ color: colors.textMuted, fontSize: 13, fontWeight: 500 }}>
          Showing <strong style={{ color: colors.textPrimary }}>{filtered.length}</strong> calculation methods
        </span>
      </div>

      {loading && <div style={{ color: colors.textMuted, padding: 20 }}>Loading logic registry...</div>}

      {!loading && renderTable(implemented, "AVAILABLE (IMPLEMENTED)")}
      {!loading && renderTable(notImplemented, "DOCUMENTED BUT NOT IMPLEMENTED (UNAVAILABLE)")}

    </div>
  );
}
