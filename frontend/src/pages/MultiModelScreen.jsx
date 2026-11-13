import React, { useState, useEffect, useMemo } from 'react';
import { useTheme } from '../context/ThemeContext';
import { 
  ResponsiveContainer, 
  ScatterChart, 
  Scatter, 
  XAxis, 
  YAxis, 
  ZAxis, 
  Tooltip, 
  CartesianGrid, 
  ReferenceLine,
  LineChart,
  Line,
  Legend
} from 'recharts';

export default function MultiModelScreen() {
  const { colors } = useTheme();

  // Mode Selection: 'all_ml', 'all_logic', 'custom'
  const [evalMode, setEvalMode] = useState('all_ml');
  const [passThreshold, setPassThreshold] = useState(75); // User requested 75% accuracy
  const [datasetType, setDatasetType] = useState('new_test'); // 'trained_data' vs 'new_test'

  // Targets & Models available
  const [allTargets, setAllTargets] = useState([]);
  const [selectedTargets, setSelectedTargets] = useState(['ALL']);
  const [allModels, setAllModels] = useState([]);
  const [allLogics, setAllLogics] = useState([]);
  const [selectedCustomMethods, setSelectedCustomMethods] = useState([]);

  // File & execution state
  const [file, setFile] = useState(null);
  const [running, setRunning] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [summaryData, setSummaryData] = useState([]);
  const [chartSeriesMap, setChartSeriesMap] = useState({});
  const [reportUrl, setReportUrl] = useState('');

  // Filtering & Sorting for representation
  const [filterNutrient, setFilterNutrient] = useState('');
  const [filterMethod, setFilterMethod] = useState('');
  const [chartType, setChartType] = useState('line'); // 'scatter' or 'line'
  const [sortBy, setSortBy] = useState('accuracy'); // 'accuracy', 'pass_rate', 'mae'
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    // Fetch available targets
    fetch(import.meta.env.BASE_URL + 'api/targets')
      .then(res => res.json())
      .then(data => {
        setAllTargets(data || []);
      })
      .catch(err => console.error('Error fetching targets:', err));

    // Fetch models
    fetch(import.meta.env.BASE_URL + 'api/models')
      .then(res => res.json())
      .then(data => {
        setAllModels(data || []);
      })
      .catch(err => console.error('Error fetching models:', err));

    // Fetch logics
    fetch(import.meta.env.BASE_URL + 'api/logics')
      .then(res => res.json())
      .then(data => {
        setAllLogics(data || []);
      })
      .catch(err => console.error('Error fetching logics:', err));
  }, []);

  const handleTargetToggle = (target) => {
    if (target === 'ALL') {
      setSelectedTargets(['ALL']);
      return;
    }
    let updated = selectedTargets.filter(t => t !== 'ALL');
    if (updated.includes(target)) {
      updated = updated.filter(t => t !== target);
      if (updated.length === 0) updated = ['ALL'];
    } else {
      updated.push(target);
    }
    setSelectedTargets(updated);
  };

  const handleCustomMethodToggle = (id, type, name) => {
    const exists = selectedCustomMethods.some(m => m.id === id);
    if (exists) {
      setSelectedCustomMethods(selectedCustomMethods.filter(m => m.id !== id));
    } else {
      setSelectedCustomMethods([...selectedCustomMethods, { id, type, name }]);
    }
  };

  const handleQuickSelectChampions = () => {
    const championIds = ['B01_PLSR', 'B07_3D_SVR', 'B09_BayesianRidge', 'B28_BoundaryBuffer', 'B24_Heterogeneous_TwoStage', 'B26_BalancedTertiles'];
    const selected = allModels
      .filter(m => championIds.includes(m.id))
      .map(m => ({ id: m.id, type: 'ml', name: m.name }));
    setSelectedCustomMethods(selected);
  };

  const handleSelectAllML = () => {
    setSelectedCustomMethods(allModels.map(m => ({ id: m.id, type: 'ml', name: m.name })));
  };

  const handleSelectAllLogics = () => {
    setSelectedCustomMethods(allLogics.map(l => ({ id: l.id, type: 'logic', name: l.name || l.id })));
  };

  const handleClearSelection = () => {
    setSelectedCustomMethods([]);
  };

  const handleRunEvaluation = async () => {
    if (!file) {
      alert('Please upload an Excel file containing soil samples (.xlsx)');
      return;
    }

    if (evalMode === 'custom' && selectedCustomMethods.length === 0) {
      alert('Please select at least 1 Model or Mathematical Logic from the selection box below (or click "✨ Fast Champions").');
      return;
    }

    setRunning(true);
    setStatusMsg(`Running evaluation on ${datasetType === 'trained_data' ? 'Training Data' : 'New Unseen Test Data'} with ${passThreshold}% pass threshold...`);
    setSummaryData([]);
    setChartSeriesMap({});
    setReportUrl('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', evalMode);
    formData.append('pass_threshold', passThreshold);
    formData.append('dataset_type', datasetType);
    formData.append('targets', JSON.stringify(selectedTargets));
    formData.append('methods', JSON.stringify(selectedCustomMethods));

    try {
      const res = await fetch(import.meta.env.BASE_URL + 'api/models/multi-eval', {
        method: 'POST',
        body: formData
      });

      // Guard against non-JSON responses (e.g. Render HTTP 504 / 502 HTML Gateway Timeout error pages)
      const contentType = res.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        const textErr = await res.text();
        if (res.status === 504 || res.status === 502) {
          throw new Error('Server computation timed out (HTTP ' + res.status + '). Evaluating all 76 models at once exceeded the server gateway limit. Tip: Select "Select Specific Models / Logics" to run models in batches of 5-10.');
        }
        throw new Error(`Server returned HTTP ${res.status}: ${textErr.slice(0, 150)}...`);
      }

      const data = await res.json();
      if (res.ok && data.success) {
        setStatusMsg(`Evaluation Complete! Evaluated ${data.summary.length} model-nutrient combinations on ${datasetType === 'trained_data' ? 'Trained Data' : 'New Validation Test Data'}.`);
        setSummaryData(data.summary || []);
        setChartSeriesMap(data.chart_series_map || {});
        if (data.report_url) {
          setReportUrl(data.report_url);
        }
        if (data.summary.length > 0) {
          // Select first nutrient and its best model
          const firstNut = data.summary[0].nutrient;
          setFilterNutrient(firstNut);
          const nutRows = data.summary.filter(s => s.nutrient === firstNut);
          nutRows.sort((a, b) => b.avg_accuracy_pct - a.avg_accuracy_pct || b.pass_rate_pct - a.pass_rate_pct);
          setFilterMethod(nutRows[0]?.method_id || data.summary[0].method_id);
        }
      } else {
        setStatusMsg(`Error: ${data.error || 'Evaluation failed'}`);
      }
    } catch (err) {
      setStatusMsg(`Error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  // Distinct evaluated nutrients
  const evaluatedNutrients = useMemo(() => {
    return [...new Set(summaryData.map(s => s.nutrient))];
  }, [summaryData]);

  // Top model for each nutrient (arranged highest to lowest accuracy)
  const topModelsByNutrient = useMemo(() => {
    const map = {};
    evaluatedNutrients.forEach(nut => {
      const list = summaryData.filter(s => s.nutrient === nut);
      list.sort((a, b) => b.avg_accuracy_pct - a.avg_accuracy_pct || b.pass_rate_pct - a.pass_rate_pct || a.mae - b.mae);
      if (list.length > 0) {
        map[nut] = list[0];
      }
    });
    return map;
  }, [summaryData, evaluatedNutrients]);

  // Active nutrient for chart display (must be a specific nutrient, not 'ALL')
  const activeChartNutrient = useMemo(() => {
    if (filterNutrient && filterNutrient !== 'ALL') return filterNutrient;
    return evaluatedNutrients[0] || 'OC';
  }, [filterNutrient, evaluatedNutrients]);

  // Current best model for the active chart nutrient
  const currentBestModel = useMemo(() => {
    return topModelsByNutrient[activeChartNutrient] || null;
  }, [topModelsByNutrient, activeChartNutrient]);

  // Switch nutrient handler: automatically focuses on top-performing model
  const handleSelectNutrientTab = (nut) => {
    setFilterNutrient(nut);
    const targetNut = nut === 'ALL' ? (evaluatedNutrients[0] || '') : nut;
    if (targetNut && topModelsByNutrient[targetNut]) {
      setFilterMethod(topModelsByNutrient[targetNut].method_id);
    }
  };

  // Filtered and sorted models for the Leaderboard
  const displayedModels = useMemo(() => {
    let list = summaryData.filter(s => {
      const matchNut = (filterNutrient === 'ALL' || s.nutrient === filterNutrient);
      const matchSearch = searchQuery.trim() === '' || 
        s.method_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
        s.method_id.toLowerCase().includes(searchQuery.toLowerCase());
      return matchNut && matchSearch;
    });

    list.sort((a, b) => {
      if (sortBy === 'accuracy') {
        // Highest accuracy to lowest accuracy
        return b.avg_accuracy_pct - a.avg_accuracy_pct || b.pass_rate_pct - a.pass_rate_pct || a.mae - b.mae;
      }
      if (sortBy === 'pass_rate') {
        return b.pass_rate_pct - a.pass_rate_pct || b.avg_accuracy_pct - a.avg_accuracy_pct || a.mae - b.mae;
      }
      if (sortBy === 'mae') {
        return a.mae - b.mae || b.avg_accuracy_pct - a.avg_accuracy_pct;
      }
      return 0;
    });

    return list;
  }, [summaryData, filterNutrient, searchQuery, sortBy]);

  // Active points for graph
  const activeKey = `${filterMethod}::${activeChartNutrient}`;
  const activePoints = chartSeriesMap[activeKey] || [];

  // Line chart data
  const lineChartData = activePoints.map((p, idx) => ({
    sample: `S${idx + 1}`,
    Actual: p.x,
    Predicted: p.y,
    accuracy: p.acc,
    passed: p.passed
  }));

  // Min/max for scatter reference diagonal line
  let minVal = 0, maxVal = 10;
  if (activePoints.length > 0) {
    const allVals = activePoints.flatMap(p => [p.x, p.y]);
    minVal = Math.floor(Math.min(...allVals));
    maxVal = Math.ceil(Math.max(...allVals));
    if (minVal === maxVal) maxVal = minVal + 1;
  }

  // Current active model statistics
  const currentStat = summaryData.find(s => s.method_id === filterMethod && s.nutrient === activeChartNutrient);

  // Helper for visual representation of accuracy
  const getAccuracyBadge = (acc) => {
    if (acc >= 85) {
      return {
        bg: '#10b981',
        barGradient: 'linear-gradient(90deg, #10b981, #059669)',
        lightBg: '#dcfce7',
        textColor: '#15803d',
        label: 'Excellent'
      };
    }
    if (acc >= 75) {
      return {
        bg: '#0284c7',
        barGradient: 'linear-gradient(90deg, #0284c7, #0369a1)',
        lightBg: '#e0f2fe',
        textColor: '#0369a1',
        label: 'Optimal (≥75%)'
      };
    }
    if (acc >= 60) {
      return {
        bg: '#f59e0b',
        barGradient: 'linear-gradient(90deg, #f59e0b, #d97706)',
        lightBg: '#fef3c7',
        textColor: '#b45309',
        label: 'Moderate'
      };
    }
    return {
      bg: '#ef4444',
      barGradient: 'linear-gradient(90deg, #ef4444, #dc2626)',
      lightBg: '#fee2e2',
      textColor: '#b91c1c',
      label: 'Sub-Optimal'
    };
  };

  return (
    <div style={{ maxWidth: 1240, margin: '0 auto', paddingBottom: 60 }}>
      {/* Header */}
      <div style={{
        background: colors.cardBg,
        border: `1px solid ${colors.cardBorder}`,
        borderRadius: 14,
        padding: '24px 28px',
        marginBottom: 24,
        boxShadow: colors.cardShadow
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: colors.textPrimary, margin: '0 0 6px 0' }}>
              🔬 Multi-Model Evaluation & Testing Screen
            </h1>
            <p style={{ margin: 0, color: colors.textSecondary, fontSize: 14 }}>
              Execute all ML algorithms or mathematical logics at once for single or multiple nutrients. Inspect accuracy pass rates, view live Actual vs Predicted graphs, and rank all models from highest to lowest accuracy.
            </p>
          </div>
          {reportUrl && (
            <a
              href={reportUrl}
              download
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: '#10b981',
                color: '#fff',
                padding: '10px 20px',
                borderRadius: 8,
                fontWeight: 700,
                fontSize: 14,
                textDecoration: 'none',
                boxShadow: '0 2px 6px rgba(16, 185, 129, 0.3)'
              }}
            >
              📥 Download Excel Report with Scatter Graphs
            </a>
          )}
        </div>
      </div>

      {/* Control Panel Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20, marginBottom: 24 }}>
        
        {/* Card 1: Execution Mode & Data Origin */}
        <div style={{
          background: colors.cardBg,
          border: `1px solid ${colors.cardBorder}`,
          borderRadius: 12,
          padding: 20,
          boxShadow: colors.cardShadow
        }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: colors.textPrimary, margin: '0 0 12px 0' }}>
            1. Execution Mode & Data Origin
          </h3>

          <div style={{
            background: colors.name === 'dark' ? '#1e293b' : '#f0fdf4',
            border: `1px solid ${colors.name === 'dark' ? '#334155' : '#bbf7d0'}`,
            borderRadius: 8,
            padding: 12,
            marginBottom: 14
          }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: colors.textPrimary, marginBottom: 6 }}>
              Are you testing same trained data or new test data?
            </label>
            <div style={{ display: 'flex', gap: 16 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer', color: colors.textPrimary }}>
                <input
                  type="radio"
                  name="datasetType"
                  value="new_test"
                  checked={datasetType === 'new_test'}
                  onChange={() => setDatasetType('new_test')}
                />
                <span><strong>🆕 New Test Data</strong> (Unseen)</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer', color: colors.textPrimary }}>
                <input
                  type="radio"
                  name="datasetType"
                  value="trained_data"
                  checked={datasetType === 'trained_data'}
                  onChange={() => setDatasetType('trained_data')}
                />
                <span><strong>🔄 Same Trained Data</strong></span>
              </label>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 14 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 13, color: colors.textPrimary }}>
              <input
                type="radio"
                name="evalMode"
                value="all_ml"
                checked={evalMode === 'all_ml'}
                onChange={() => setEvalMode('all_ml')}
              />
              <span><strong>⚡ Run All ML Algorithms Once</strong> ({allModels.length} Models)</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 13, color: colors.textPrimary }}>
              <input
                type="radio"
                name="evalMode"
                value="all_logic"
                checked={evalMode === 'all_logic'}
                onChange={() => setEvalMode('all_logic')}
              />
              <span><strong>📐 Run All Mathematical Logics Once</strong> ({allLogics.length} Logics)</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 13, color: colors.textPrimary }}>
              <input
                type="radio"
                name="evalMode"
                value="custom"
                checked={evalMode === 'custom'}
                onChange={() => setEvalMode('custom')}
              />
              <span><strong>🎯 Select Specific Models / Logics</strong></span>
            </label>
          </div>

          <div style={{ borderTop: `1px solid ${colors.cardBorder}`, paddingTop: 10 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: colors.textPrimary, marginBottom: 4 }}>
              Sample Accuracy Pass Threshold: <span style={{ color: '#0284c7', fontSize: 15, fontWeight: 700 }}>{passThreshold}%</span>
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <input
                type="range"
                min="50"
                max="95"
                step="5"
                value={passThreshold}
                onChange={e => setPassThreshold(Number(e.target.value))}
                style={{ flex: 1, cursor: 'pointer' }}
              />
              <span style={{ fontSize: 12, color: colors.textSecondary, whiteSpace: 'nowrap' }}>
                (Err ≤ {100 - passThreshold}%)
              </span>
            </div>
            <div style={{ fontSize: 11, color: colors.textSecondary, marginTop: 4 }}>
              A sample passes if accuracy is at least <strong>{passThreshold}%</strong>.
            </div>
          </div>
        </div>

        {/* Card 2: Target Nutrient Selection */}
        <div style={{
          background: colors.cardBg,
          border: `1px solid ${colors.cardBorder}`,
          borderRadius: 12,
          padding: 20,
          boxShadow: colors.cardShadow
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>
              2. Target Nutrient(s)
            </h3>
            <span style={{ fontSize: 12, color: colors.textSecondary }}>
              {selectedTargets.includes('ALL') ? 'All Nutrients' : `${selectedTargets.length} Selected`}
            </span>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 190, overflowY: 'auto', padding: 4 }}>
            <button
              onClick={() => handleTargetToggle('ALL')}
              style={{
                fontSize: 12,
                padding: '6px 14px',
                borderRadius: 20,
                border: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                background: selectedTargets.includes('ALL') ? '#0284c7' : colors.bg,
                color: selectedTargets.includes('ALL') ? '#fff' : colors.textPrimary,
                border: `1px solid ${selectedTargets.includes('ALL') ? '#0284c7' : colors.cardBorder}`
              }}
            >
              ★ All Nutrients
            </button>
            {allTargets.map(t => {
              const active = selectedTargets.includes(t);
              return (
                <button
                  key={t}
                  onClick={() => handleTargetToggle(t)}
                  style={{
                    fontSize: 12,
                    padding: '6px 12px',
                    borderRadius: 20,
                    cursor: 'pointer',
                    fontWeight: 500,
                    background: active ? '#0284c7' : colors.bg,
                    color: active ? '#fff' : colors.textPrimary,
                    border: `1px solid ${active ? '#0284c7' : colors.cardBorder}`
                  }}
                >
                  {t}
                </button>
              );
            })}
          </div>
        </div>

        {/* Card 3: File Upload & Action Button */}
        <div style={{
          background: colors.cardBg,
          border: `1px solid ${colors.cardBorder}`,
          borderRadius: 12,
          padding: 20,
          boxShadow: colors.cardShadow,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}>
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: colors.textPrimary, margin: '0 0 10px 0' }}>
              3. Upload Test File & Run
            </h3>
            <p style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 12 }}>
              Upload Excel sheet with spectral inputs (`nm_...`) and laboratory reference values.
            </p>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={e => setFile(e.target.files[0])}
              style={{ fontSize: 12, color: colors.textPrimary, marginBottom: 16, width: '100%' }}
            />
          </div>

          <button
            onClick={handleRunEvaluation}
            disabled={running || !file}
            style={{
              background: running ? '#9ca3af' : '#0284c7',
              color: '#fff',
              border: 'none',
              padding: '12px 24px',
              borderRadius: 8,
              fontSize: 15,
              fontWeight: 700,
              cursor: running || !file ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 10,
              boxShadow: '0 2px 6px rgba(2, 132, 199, 0.3)'
            }}
          >
            {running
              ? '⏳ Evaluating Chemometrics...'
              : evalMode === 'custom'
                ? `🎯 Execute Selected Methods (${selectedCustomMethods.length})`
                : evalMode === 'all_logic'
                  ? '📐 Execute All 51 Mathematical Logics'
                  : '⚡ Execute All 76 ML Models'
            }
          </button>
        </div>

      </div>

      {/* Custom Method Selection Panel */}
      {evalMode === 'custom' && (
        <div style={{
          background: colors.cardBg,
          border: `1px solid ${colors.cardBorder}`,
          borderRadius: 12,
          padding: 20,
          marginBottom: 24,
          boxShadow: colors.cardShadow
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10, marginBottom: 14 }}>
            <div>
              <h4 style={{ fontSize: 15, fontWeight: 700, color: colors.textPrimary, margin: '0 0 4px 0' }}>
                Select Specific Models / Logics to Benchmark:
              </h4>
              <span style={{ fontSize: 12, color: colors.textSecondary }}>
                Selected: <strong style={{ color: '#0284c7' }}>{selectedCustomMethods.length}</strong> items (Running in batches of 4–10 prevents gateway timeouts)
              </span>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={handleQuickSelectChampions}
                style={{
                  background: '#0284c7',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 6,
                  padding: '6px 12px',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                ✨ Select Top 6 Fast Champions
              </button>
              <button
                type="button"
                onClick={handleSelectAllML}
                style={{
                  background: colors.bg,
                  color: colors.textPrimary,
                  border: `1px solid ${colors.cardBorder}`,
                  borderRadius: 6,
                  padding: '6px 12px',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                All ML ({allModels.length})
              </button>
              <button
                type="button"
                onClick={handleClearSelection}
                style={{
                  background: 'transparent',
                  color: '#ef4444',
                  border: '1px solid #ef4444',
                  borderRadius: 6,
                  padding: '6px 12px',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Clear
              </button>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8, maxHeight: 220, overflowY: 'auto', padding: 4 }}>
            {allModels.map(m => {
              const sel = selectedCustomMethods.some(x => x.id === m.id);
              return (
                <div
                  key={m.id}
                  onClick={() => handleCustomMethodToggle(m.id, 'ml', m.name)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 6,
                    fontSize: 12,
                    cursor: 'pointer',
                    background: sel ? '#0284c7' : colors.bg,
                    color: sel ? '#fff' : colors.textPrimary,
                    border: `1px solid ${sel ? '#0284c7' : colors.cardBorder}`,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}
                  title={m.name}
                >
                  🤖 {m.name}
                </div>
              );
            })}
            {allLogics.map(l => {
              const sel = selectedCustomMethods.some(x => x.id === l.id);
              return (
                <div
                  key={l.id}
                  onClick={() => handleCustomMethodToggle(l.id, 'logic', l.name || l.id)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 6,
                    fontSize: 12,
                    cursor: 'pointer',
                    background: sel ? '#16a34a' : colors.bg,
                    color: sel ? '#fff' : colors.textPrimary,
                    border: `1px solid ${sel ? '#16a34a' : colors.cardBorder}`,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}
                  title={l.name || l.id}
                >
                  📐 {l.id} - {l.name || 'Logic'}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Status banner */}
      {statusMsg && (
        <div style={{
          padding: 14,
          borderRadius: 8,
          marginBottom: 24,
          fontSize: 14,
          fontWeight: 600,
          background: statusMsg.includes('Error') ? '#fee2e2' : '#dcfce7',
          color: statusMsg.includes('Error') ? '#991b1b' : '#166534',
          border: `1px solid ${statusMsg.includes('Error') ? '#fca5a5' : '#86efac'}`
        }}>
          {statusMsg}
        </div>
      )}

      {/* Results View */}
      {summaryData.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* ─────────────────────────────────────────────────────────── */}
          {/* SECTION 1: PROMINENT NUTRIENT SELECTION & FILTER BAR         */}
          {/* ─────────────────────────────────────────────────────────── */}
          <div style={{
            background: colors.cardBg,
            border: `1px solid ${colors.cardBorder}`,
            borderRadius: 14,
            padding: '20px 24px',
            boxShadow: colors.cardShadow,
            display: 'flex',
            flexDirection: 'column',
            gap: 14
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: colors.textPrimary, display: 'flex', alignItems: 'center', gap: 8 }}>
                  🎯 Select Nutrient to View Ranked Models
                </h3>
                <p style={{ margin: '4px 0 0 0', fontSize: 13, color: colors.textSecondary }}>
                  Select any nutrient (e.g. <strong>OC</strong>, <strong>P</strong>, <strong>K</strong>) to view how much accuracy every model achieved, arranged from highest to lowest.
                </p>
              </div>
              <div style={{
                fontSize: 13,
                fontWeight: 700,
                color: colors.textPrimary,
                background: colors.bg,
                padding: '6px 14px',
                borderRadius: 20,
                border: `1px solid ${colors.cardBorder}`
              }}>
                Active View: <span style={{ color: '#0284c7', fontWeight: 800 }}>{filterNutrient === 'ALL' ? '⭐ All Nutrients' : `🌿 ${filterNutrient}`}</span>
              </div>
            </div>

            {/* Nutrient Quick Switch Pills */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
              <button
                onClick={() => handleSelectNutrientTab('ALL')}
                style={{
                  padding: '9px 18px',
                  borderRadius: 24,
                  cursor: 'pointer',
                  fontSize: 13,
                  fontWeight: 700,
                  background: filterNutrient === 'ALL' ? '#0284c7' : colors.bg,
                  color: filterNutrient === 'ALL' ? '#fff' : colors.textPrimary,
                  border: `1px solid ${filterNutrient === 'ALL' ? '#0284c7' : colors.cardBorder}`,
                  boxShadow: filterNutrient === 'ALL' ? '0 2px 8px rgba(2, 132, 199, 0.35)' : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  transition: 'all 0.2s ease'
                }}
              >
                <span>⭐ All Nutrients</span>
                <span style={{
                  fontSize: 11,
                  padding: '1px 7px',
                  borderRadius: 10,
                  background: filterNutrient === 'ALL' ? 'rgba(255,255,255,0.25)' : (colors.name === 'dark' ? '#334155' : '#e2e8f0'),
                  color: filterNutrient === 'ALL' ? '#fff' : colors.textSecondary
                }}>
                  {summaryData.length}
                </span>
              </button>

              {evaluatedNutrients.map(nut => {
                const isSel = filterNutrient === nut;
                const topM = topModelsByNutrient[nut];
                const count = summaryData.filter(s => s.nutrient === nut).length;
                return (
                  <button
                    key={nut}
                    onClick={() => handleSelectNutrientTab(nut)}
                    style={{
                      padding: '9px 18px',
                      borderRadius: 24,
                      cursor: 'pointer',
                      fontSize: 13,
                      fontWeight: 700,
                      background: isSel ? '#10b981' : colors.bg,
                      color: isSel ? '#fff' : colors.textPrimary,
                      border: `1px solid ${isSel ? '#10b981' : colors.cardBorder}`,
                      boxShadow: isSel ? '0 2px 10px rgba(16, 185, 129, 0.4)' : 'none',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <span>{nut}</span>
                    {topM && (
                      <span style={{
                        fontSize: 11,
                        fontWeight: 800,
                        padding: '2px 8px',
                        borderRadius: 10,
                        background: isSel ? 'rgba(255,255,255,0.3)' : (colors.name === 'dark' ? '#1e293b' : '#f0fdf4'),
                        color: isSel ? '#fff' : '#15803d'
                      }}>
                        Top: {topM.avg_accuracy_pct}%
                      </span>
                    )}
                    <span style={{
                      fontSize: 11,
                      color: isSel ? 'rgba(255,255,255,0.85)' : colors.textMuted
                    }}>
                      ({count})
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* ─────────────────────────────────────────────────────────── */}
          {/* SECTION 2: MULTI-NUTRIENT OVERVIEW GRID (when ALL selected)  */}
          {/* ─────────────────────────────────────────────────────────── */}
          {filterNutrient === 'ALL' && evaluatedNutrients.length > 1 && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
              gap: 14
            }}>
              {evaluatedNutrients.map(nut => {
                const topM = topModelsByNutrient[nut];
                if (!topM) return null;
                const count = summaryData.filter(s => s.nutrient === nut).length;
                return (
                  <div
                    key={nut}
                    onClick={() => handleSelectNutrientTab(nut)}
                    style={{
                      background: colors.cardBg,
                      border: `1px solid ${colors.cardBorder}`,
                      borderRadius: 12,
                      padding: 16,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      boxShadow: colors.cardShadow,
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between'
                    }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = '#10b981'}
                    onMouseLeave={e => e.currentTarget.style.borderColor = colors.cardBorder}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <span style={{ fontSize: 18, fontWeight: 800, color: colors.textPrimary }}>{nut}</span>
                      <span style={{
                        fontSize: 13,
                        fontWeight: 800,
                        padding: '4px 10px',
                        borderRadius: 6,
                        background: '#dcfce7',
                        color: '#15803d'
                      }}>
                        Top: {topM.avg_accuracy_pct}%
                      </span>
                    </div>
                    <div style={{ fontSize: 13, color: colors.textSecondary, marginBottom: 8, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      Best: <strong style={{ color: colors.textPrimary }}>{topM.method_name}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: colors.textMuted, borderTop: `1px solid ${colors.cardBorder}`, paddingTop: 8 }}>
                      <span>Pass: <strong>{topM.pass_rate_pct}%</strong></span>
                      <span style={{ color: '#0284c7', fontWeight: 700 }}>Inspect {count} Models →</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────── */}
          {/* SECTION 3: TOP-PERFORMING MODEL SPOTLIGHT HERO BANNER         */}
          {/* ─────────────────────────────────────────────────────────── */}
          {currentBestModel && (
            <div style={{
              background: colors.name === 'dark' 
                ? 'linear-gradient(135deg, #064e3b 0%, #0f172a 100%)' 
                : 'linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%)',
              border: '2px solid #10b981',
              borderRadius: 14,
              padding: '20px 24px',
              boxShadow: '0 4px 16px rgba(16, 185, 129, 0.18)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 16
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
                <div style={{
                  width: 52,
                  height: 52,
                  borderRadius: 14,
                  background: '#10b981',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 26,
                  boxShadow: '0 3px 10px rgba(16, 185, 129, 0.4)'
                }}>
                  👑
                </div>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.6, color: '#10b981' }}>
                    #1 Highest Accuracy Model for {activeChartNutrient}
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: colors.textPrimary, margin: '2px 0' }}>
                    {currentBestModel.method_name}
                  </div>
                  <div style={{ fontSize: 12, color: colors.textSecondary }}>
                    Architecture: <strong>{currentBestModel.method_type}</strong> | Samples Tested: <strong>{currentBestModel.total_samples}</strong> | MAE Error: <strong>± {currentBestModel.mae}</strong>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
                <div style={{
                  textAlign: 'center',
                  background: colors.cardBg,
                  padding: '10px 18px',
                  borderRadius: 10,
                  border: `1px solid ${colors.cardBorder}`,
                  boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
                }}>
                  <div style={{ fontSize: 11, color: colors.textSecondary, fontWeight: 700 }}>AVERAGE ACCURACY</div>
                  <div style={{ fontSize: 24, fontWeight: 900, color: '#10b981' }}>
                    {currentBestModel.avg_accuracy_pct}%
                  </div>
                </div>

                <div style={{
                  textAlign: 'center',
                  background: colors.cardBg,
                  padding: '10px 18px',
                  borderRadius: 10,
                  border: `1px solid ${colors.cardBorder}`,
                  boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
                }}>
                  <div style={{ fontSize: 11, color: colors.textSecondary, fontWeight: 700 }}>PASS RATE (≥{passThreshold}%)</div>
                  <div style={{ fontSize: 24, fontWeight: 900, color: currentBestModel.pass_rate_pct >= passThreshold ? '#10b981' : '#f59e0b' }}>
                    {currentBestModel.pass_rate_pct}%
                  </div>
                </div>

                <button
                  onClick={() => setFilterMethod(currentBestModel.method_id)}
                  style={{
                    background: filterMethod === currentBestModel.method_id ? '#10b981' : colors.cardBg,
                    color: filterMethod === currentBestModel.method_id ? '#fff' : '#10b981',
                    border: '1px solid #10b981',
                    padding: '12px 20px',
                    borderRadius: 8,
                    fontWeight: 700,
                    fontSize: 13,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6
                  }}
                >
                  {filterMethod === currentBestModel.method_id ? '✓ Active in Graph' : '📈 View Graph'}
                </button>
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────── */}
          {/* SECTION 4: INTERACTIVE GRAPH (ACTUAL VS PREDICTED)          */}
          {/* ─────────────────────────────────────────────────────────── */}
          <div style={{
            background: colors.cardBg,
            border: `1px solid ${colors.cardBorder}`,
            borderRadius: 14,
            padding: 24,
            boxShadow: colors.cardShadow
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: colors.textPrimary }}>
                  📈 Actual vs Predicted Graph ({activeChartNutrient} — {currentStat?.method_name || filterMethod})
                </h3>
                <span style={{ fontSize: 13, color: colors.textSecondary }}>
                  {currentStat ? (
                    <span>
                      Avg Accuracy: <strong style={{ color: '#10b981', fontSize: 14 }}>{currentStat.avg_accuracy_pct}%</strong> | Pass Rate: <strong style={{ color: currentStat.pass_rate_pct >= passThreshold ? '#10b981' : '#ef4444' }}>{currentStat.pass_rate_pct}%</strong> ({currentStat.passed_samples}/{currentStat.total_samples} samples ≥ {passThreshold}%) | MAE: <strong>± {currentStat.mae}</strong>
                    </span>
                  ) : 'Select a nutrient and model below'}
                </span>
              </div>

              {/* Chart Filters & Display Toggle */}
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                <div>
                  <label style={{ fontSize: 11, color: colors.textSecondary, display: 'block', fontWeight: 600 }}>Nutrient:</label>
                  <select
                    value={activeChartNutrient}
                    onChange={e => handleSelectNutrientTab(e.target.value)}
                    style={{ padding: '6px 12px', borderRadius: 6, border: `1px solid ${colors.cardBorder}`, background: colors.bg, color: colors.textPrimary, fontSize: 13, fontWeight: 600 }}
                  >
                    {evaluatedNutrients.map(n => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: 11, color: colors.textSecondary, display: 'block', fontWeight: 600 }}>Model (Arranged Highest to Lowest):</label>
                  <select
                    value={filterMethod}
                    onChange={e => setFilterMethod(e.target.value)}
                    style={{ padding: '6px 12px', borderRadius: 6, border: `1px solid ${colors.cardBorder}`, background: colors.bg, color: colors.textPrimary, fontSize: 13, maxWidth: 320, fontWeight: 600 }}
                  >
                    {summaryData
                      .filter(s => s.nutrient === activeChartNutrient)
                      .sort((a, b) => b.avg_accuracy_pct - a.avg_accuracy_pct)
                      .map((s, sIdx) => (
                        <option key={s.method_id} value={s.method_id}>
                          #{sIdx + 1} {s.method_name} — {s.avg_accuracy_pct}% Acc ({s.pass_rate_pct}% Pass)
                        </option>
                      ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: 11, color: colors.textSecondary, display: 'block', fontWeight: 600 }}>Graph Type:</label>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button
                      onClick={() => setChartType('scatter')}
                      style={{
                        padding: '6px 12px',
                        borderRadius: 6,
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: 12,
                        fontWeight: 600,
                        background: chartType === 'scatter' ? '#0284c7' : colors.bg,
                        color: chartType === 'scatter' ? '#fff' : colors.textPrimary,
                        border: `1px solid ${chartType === 'scatter' ? '#0284c7' : colors.cardBorder}`
                      }}
                    >
                      Scatter Plot
                    </button>
                    <button
                      onClick={() => setChartType('line')}
                      style={{
                        padding: '6px 12px',
                        borderRadius: 6,
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: 12,
                        fontWeight: 600,
                        background: chartType === 'line' ? '#0284c7' : colors.bg,
                        color: chartType === 'line' ? '#fff' : colors.textPrimary,
                        border: `1px solid ${chartType === 'line' ? '#0284c7' : colors.cardBorder}`
                      }}
                    >
                      Line with Points
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Chart Rendering */}
            <div style={{ width: '100%', height: 420 }}>
              {activePoints.length === 0 ? (
                <div style={{ padding: 40, textAlign: 'center', color: colors.textMuted }}>
                  No sample data points available for this combination.
                </div>
              ) : chartType === 'scatter' ? (
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 30, bottom: 25, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.cardBorder} />
                    <XAxis 
                      type="number" 
                      dataKey="x" 
                      name="Actual Value" 
                      stroke={colors.textSecondary}
                      domain={['dataMin - 1', 'dataMax + 1']}
                      label={{ value: `Actual Laboratory ${activeChartNutrient}`, position: 'insideBottom', offset: -15, fill: colors.textSecondary, fontSize: 12 }}
                    />
                    <YAxis 
                      type="number" 
                      dataKey="y" 
                      name="Predicted Value" 
                      stroke={colors.textSecondary}
                      domain={['dataMin - 1', 'dataMax + 1']}
                      label={{ value: `Predicted ${activeChartNutrient}`, angle: -90, position: 'insideLeft', fill: colors.textSecondary, fontSize: 12 }}
                    />
                    <ZAxis range={[70, 70]} />
                    <Tooltip 
                      cursor={{ strokeDasharray: '3 3' }} 
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div style={{ background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, padding: '10px 14px', borderRadius: 8, fontSize: 12, color: colors.textPrimary, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
                              <div style={{ fontWeight: 700, marginBottom: 4 }}>Sample Point</div>
                              <div>Actual: <strong>{data.x}</strong></div>
                              <div>Predicted: <strong>{data.y}</strong></div>
                              <div>Accuracy: <strong style={{ color: data.passed ? '#10b981' : '#ef4444' }}>{data.acc}%</strong></div>
                              <div>Status: {data.passed ? `✅ Passed (≥${passThreshold}%)` : `❌ Below ${passThreshold}%`}</div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <ReferenceLine 
                      segment={[{ x: minVal, y: minVal }, { x: maxVal, y: maxVal }]} 
                      stroke="#9ca3af" 
                      strokeDasharray="4 4" 
                      label={{ value: 'Ideal (1:1)', fill: '#9ca3af', position: 'top', fontSize: 11 }} 
                    />
                    <Scatter 
                      name="Predicted Samples" 
                      data={activePoints} 
                      fill="#0284c7"
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={lineChartData} margin={{ top: 20, right: 30, bottom: 25, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.cardBorder} />
                    <XAxis dataKey="sample" stroke={colors.textSecondary} />
                    <YAxis stroke={colors.textSecondary} />
                    <Tooltip contentStyle={{ backgroundColor: colors.cardBg, borderColor: colors.cardBorder, color: colors.textPrimary }} />
                    <Legend verticalAlign="top" height={36} />
                    <Line type="monotone" dataKey="Actual" stroke="#10b981" strokeWidth={2.5} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="Predicted" stroke="#0284c7" strokeWidth={2.5} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* ─────────────────────────────────────────────────────────── */}
          {/* SECTION 5: MODEL ACCURACY LEADERBOARD (HIGHEST TO LOWEST)   */}
          {/* ─────────────────────────────────────────────────────────── */}
          <div style={{
            background: colors.cardBg,
            border: `1px solid ${colors.cardBorder}`,
            borderRadius: 14,
            padding: 24,
            boxShadow: colors.cardShadow
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14, marginBottom: 18 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: colors.textPrimary, display: 'flex', alignItems: 'center', gap: 8 }}>
                  🏆 Model Accuracy Leaderboard — {filterNutrient === 'ALL' ? 'All Nutrients' : `Nutrient: ${filterNutrient}`}
                </h3>
                <span style={{ fontSize: 13, color: colors.textSecondary }}>
                  All models arranged from <strong>highest to lowest</strong> for clear evaluation. Click any model to view its Actual vs Predicted curve above.
                </span>
              </div>

              {/* Sort & Search Controls */}
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                <input
                  type="text"
                  placeholder="🔍 Search model..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  style={{
                    padding: '7px 12px',
                    borderRadius: 8,
                    border: `1px solid ${colors.cardBorder}`,
                    background: colors.bg,
                    color: colors.textPrimary,
                    fontSize: 13,
                    minWidth: 160
                  }}
                />

                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <label style={{ fontSize: 12, color: colors.textSecondary, fontWeight: 600 }}>Sort By:</label>
                  <select
                    value={sortBy}
                    onChange={e => setSortBy(e.target.value)}
                    style={{
                      padding: '7px 12px',
                      borderRadius: 8,
                      border: `1px solid ${colors.cardBorder}`,
                      background: colors.bg,
                      color: colors.textPrimary,
                      fontSize: 13,
                      fontWeight: 600
                    }}
                  >
                    <option value="accuracy">🥇 Accuracy % (Highest to Lowest)</option>
                    <option value="pass_rate">🎯 Pass Rate % (Highest to Lowest)</option>
                    <option value="mae">📉 MAE Error (Lowest to Highest)</option>
                  </select>
                </div>

                <span style={{ fontSize: 12, background: '#0284c7', color: '#fff', padding: '6px 12px', borderRadius: 20, fontWeight: 700 }}>
                  {displayedModels.length} Models
                </span>
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13, color: colors.textPrimary }}>
                <thead>
                  <tr style={{ background: colors.bg, borderBottom: `2px solid ${colors.cardBorder}` }}>
                    <th style={{ padding: '12px 14px', width: 80 }}>Rank</th>
                    <th style={{ padding: '12px 14px' }}>Model / Algorithm</th>
                    <th style={{ padding: '12px 14px', width: 110 }}>Type</th>
                    <th style={{ padding: '12px 14px', width: 90 }}>Nutrient</th>
                    <th style={{ padding: '12px 14px', minWidth: 200 }}>Accuracy (Highest → Lowest)</th>
                    <th style={{ padding: '12px 14px', width: 130 }}>Pass Rate (≥{passThreshold}%)</th>
                    <th style={{ padding: '12px 14px', width: 120 }}>Passed / Total</th>
                    <th style={{ padding: '12px 14px', width: 100 }}>MAE</th>
                    <th style={{ padding: '12px 14px', width: 90, textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedModels.map((row, idx) => {
                    const isSelected = (activeChartNutrient === row.nutrient && filterMethod === row.method_id);
                    const accBadge = getAccuracyBadge(row.avg_accuracy_pct);
                    const isHighPass = row.pass_rate_pct >= passThreshold;

                    return (
                      <tr 
                        key={`${row.method_id}-${row.nutrient}`}
                        onClick={() => {
                          setFilterNutrient(row.nutrient);
                          setFilterMethod(row.method_id);
                        }}
                        style={{
                          borderBottom: `1px solid ${colors.cardBorder}`,
                          cursor: 'pointer',
                          background: isSelected 
                            ? (colors.name === 'dark' ? 'rgba(2, 132, 199, 0.22)' : '#e0f2fe') 
                            : 'transparent',
                          transition: 'background 0.15s ease'
                        }}
                      >
                        {/* Rank with Medals */}
                        <td style={{ padding: '12px 14px', fontWeight: 800 }}>
                          {idx === 0 ? (
                            <span style={{ fontSize: 15, color: '#eab308' }}>🥇 1</span>
                          ) : idx === 1 ? (
                            <span style={{ fontSize: 15, color: '#94a3b8' }}>🥈 2</span>
                          ) : idx === 2 ? (
                            <span style={{ fontSize: 15, color: '#b45309' }}>🥉 3</span>
                          ) : (
                            <span style={{ color: colors.textSecondary }}>#{idx + 1}</span>
                          )}
                        </td>

                        {/* Model / Algorithm Name */}
                        <td style={{ padding: '12px 14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontWeight: 700, color: colors.textPrimary, fontSize: 14 }}>
                              {row.method_name}
                            </span>
                            {isSelected && (
                              <span style={{
                                fontSize: 10,
                                padding: '2px 6px',
                                borderRadius: 4,
                                background: '#0284c7',
                                color: '#fff',
                                fontWeight: 700
                              }}>
                                Active
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: 11, color: colors.textSecondary, marginTop: 2 }}>
                            {row.method_id}
                          </div>
                        </td>

                        {/* Model Type */}
                        <td style={{ padding: '12px 14px' }}>
                          <span style={{
                            fontSize: 11,
                            padding: '3px 8px',
                            borderRadius: 6,
                            background: row.method_type.includes('Machine') ? '#ede9fe' : '#dcfce7',
                            color: row.method_type.includes('Machine') ? '#6d28d9' : '#15803d',
                            fontWeight: 700
                          }}>
                            {row.method_type.includes('Machine') ? '🤖 ML' : '📐 Logic'}
                          </span>
                        </td>

                        {/* Nutrient Badge */}
                        <td style={{ padding: '12px 14px' }}>
                          <span style={{
                            fontSize: 12,
                            fontWeight: 800,
                            padding: '3px 9px',
                            borderRadius: 6,
                            background: colors.name === 'dark' ? '#1e293b' : '#f1f5f9',
                            color: colors.textPrimary,
                            border: `1px solid ${colors.cardBorder}`
                          }}>
                            {row.nutrient}
                          </span>
                        </td>

                        {/* Accuracy: Visual progress bar + clean metric */}
                        <td style={{ padding: '12px 14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                            <span style={{ fontWeight: 800, fontSize: 15, color: accBadge.textColor }}>
                              {row.avg_accuracy_pct}%
                            </span>
                            <span style={{ fontSize: 10, fontWeight: 700, padding: '1px 6px', borderRadius: 4, background: accBadge.lightBg, color: accBadge.textColor }}>
                              {accBadge.label}
                            </span>
                          </div>
                          <div style={{ width: '100%', height: 7, borderRadius: 4, background: colors.name === 'dark' ? '#334155' : '#e2e8f0', overflow: 'hidden' }}>
                            <div style={{
                              width: `${Math.min(100, Math.max(0, row.avg_accuracy_pct))}%`,
                              height: '100%',
                              background: accBadge.barGradient,
                              borderRadius: 4,
                              transition: 'width 0.4s ease'
                            }} />
                          </div>
                        </td>

                        {/* Pass Rate % */}
                        <td style={{ padding: '12px 14px' }}>
                          <span style={{
                            color: isHighPass ? '#10b981' : '#ef4444',
                            fontWeight: 800,
                            fontSize: 14
                          }}>
                            {row.pass_rate_pct}%
                          </span>
                        </td>

                        {/* Passed / Total */}
                        <td style={{ padding: '12px 14px', fontSize: 12, color: colors.textSecondary }}>
                          <strong>{row.passed_samples}</strong> / {row.total_samples}
                        </td>

                        {/* MAE */}
                        <td style={{ padding: '12px 14px', fontSize: 12, color: colors.textSecondary, fontFamily: 'monospace' }}>
                          ± {row.mae}
                        </td>

                        {/* Action */}
                        <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setFilterNutrient(row.nutrient);
                              setFilterMethod(row.method_id);
                            }}
                            style={{
                              padding: '5px 10px',
                              borderRadius: 6,
                              fontSize: 11,
                              fontWeight: 700,
                              cursor: 'pointer',
                              border: `1px solid ${isSelected ? '#0284c7' : colors.cardBorder}`,
                              background: isSelected ? '#0284c7' : colors.bg,
                              color: isSelected ? '#fff' : colors.textPrimary
                            }}
                          >
                            {isSelected ? 'Viewing' : 'Inspect'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
