// Wavelength defaults
const WAVELENGTHS_DEFAULT = [
  { nm: 410, label: 'Violet' }, { nm: 435, label: 'Deep Blue' }, { nm: 460, label: 'Blue' },
  { nm: 485, label: 'Cyan-Blue' }, { nm: 510, label: 'Cyan' }, { nm: 535, label: 'Green' },
  { nm: 560, label: 'Yellow-Green' }, { nm: 585, label: 'Yellow' }, { nm: 610, label: 'Amber' },
  { nm: 645, label: 'Orange' }, { nm: 680, label: 'Red' }, { nm: 705, label: 'Deep Red' },
  { nm: 730, label: 'Far Red' }, { nm: 760, label: 'NIR-1' }, { nm: 810, label: 'NIR-2' },
  { nm: 860, label: 'NIR-3' }, { nm: 900, label: 'NIR-4' }, { nm: 940, label: 'NIR-5' },
  { nm: 320, label: 'UV-A' }, { nm: 280, label: 'UV-B' }, { nm: 200, label: 'UV-C' }
];

const SAMPLE_ROW = [1159.21, 208.78, 998.73, 281.32, 468.92, 923.83, 386.57, 469.43, 338.56, 94.0, 41.0, 15.0, 572.86, 183.57, 68.98, 46.0, 110.09, 356.73, 86.629, 3.611, 2.644];

let currentMethods = { logics: [], models: [] };

function init() {
  const container = document.getElementById('wavelength-inputs');
  WAVELENGTHS_DEFAULT.forEach((w, i) => {
    container.innerHTML += `
      <div class="input-group">
        <label class="input-label">nm_${w.nm} (${w.label})</label>
        <input type="number" step="any" id="wl-${i}" placeholder="0.0">
      </div>
    `;
  });
}

function loadDummyWavelengths() {
  SAMPLE_ROW.forEach((val, i) => {
    document.getElementById(`wl-${i}`).value = val;
  });
}

function switchTab(tabId) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  
  const selectedTab = Array.from(document.querySelectorAll('.tab')).find(t => t.textContent.toLowerCase().replace(/[^a-z0-9]/g,'-').includes(tabId));
  if(selectedTab) selectedTab.classList.add('active');
  
  const panel = document.getElementById(`panel-${tabId}`);
  if(panel) panel.classList.add('active');
}

async function onTargetSelect() {
  const target = document.getElementById('target-select').value;
  const methodContainer = document.getElementById('method-container');
  const validationCard = document.getElementById('validation-card');
  
  if (!target) {
    methodContainer.style.display = 'none';
    validationCard.style.display = 'none';
    return;
  }

  // Fetch available methods for target
  const res = await fetch(`/api/methods/${target}`);
  currentMethods = await res.json();

  document.getElementById('method-type-select').value = "";
  document.getElementById('method-select').innerHTML = '<option value="">-- Waiting for selection --</option>';
  
  methodContainer.style.display = 'block';
  validationCard.style.display = 'none';
}

function onMethodTypeSelect() {
  const type = document.getElementById('method-type-select').value;
  const methodSelect = document.getElementById('method-select');
  
  methodSelect.innerHTML = '<option value="">-- Select Method --</option>';
  if (type === 'logic') {
    currentMethods.logics.forEach(l => {
      methodSelect.innerHTML += `<option value="${l.id}">${l.name}</option>`;
    });
  } else if (type === 'ml') {
    currentMethods.models.forEach(m => {
      methodSelect.innerHTML += `<option value="${m.id}">${m.name}</option>`;
    });
  }
  onMethodSelect();
}

function onMethodSelect() {
  const type = document.getElementById('method-type-select').value;
  const methodId = document.getElementById('method-select').value;
  const validationCard = document.getElementById('validation-card');
  const reqWave = document.getElementById('req-wavelengths-info');
  const calInfo = document.getElementById('calibration-info');
  const calInput = document.getElementById('calibration-data-input');
  const runBtn = document.getElementById('run-btn');

  if (!methodId) {
    validationCard.style.display = 'none';
    runBtn.disabled = true;
    return;
  }

  validationCard.style.display = 'block';
  runBtn.disabled = false;

  if (type === 'logic') {
    reqWave.className = 'alert alert-success';
    reqWave.innerHTML = '✓ All 21 wavelengths supported or dynamic selection handled by logic.';
    
    calInfo.className = 'alert alert-warn';
    calInfo.innerHTML = 'Calibration Required: YES';
    calInput.style.display = 'block';
    
    // Default calibration JSON for this test
    const dummyCal = {"vals": [0.12, 0.27, 1.43], "indices": [6, 7, 18, 19, 20], "min": [1861.48, 426.04, 1551.11, 486.63, 696.82, 1124.74, 524.96, 588.01, 391.81, 107.0, 44.0, 19.0, 660.18, 198.08, 73.0, 49.75, 119.99, 368.23, 598.595, 9.22, 7.48], "mid": [1158.5, 236.86, 1101.22, 317.04, 515.5, 984.7, 422.05, 499.88, 357.4, 100.0, 42.98, 16.0, 616.93, 199.0, 72.19, 48.01, 116.98, 382.03, 94.22, 3.95, 2.85], "max": [1020.32, 211.94, 956.79, 288.0, 493.17, 919.26, 398.38, 479.16, 345.54, 95.0, 40.15, 15.0, 580.26, 186.94, 70.03, 46.19, 110.0, 363.75, 65.36, 3.71, 2.57], "value_min": 0.12, "value_mid": 0.27, "value_max": 1.43};
    calInput.value = JSON.stringify(dummyCal, null, 2);
  } else {
    reqWave.className = 'alert alert-info';
    reqWave.innerHTML = 'Will be determined dynamically from .pkl file features in backend.';
    
    calInfo.className = 'alert alert-success';
    calInfo.innerHTML = 'Calibration Required: NO';
    calInput.style.display = 'none';
  }
}

async function runPrediction() {
  const type = document.getElementById('method-type-select').value;
  const methodId = document.getElementById('method-select').value;
  const target = document.getElementById('target-select').value;
  
  let wvs = [];
  for(let i=0; i<21; i++) {
    wvs.push(parseFloat(document.getElementById(`wl-${i}`).value || 0));
  }

  let endpoint = type === 'logic' ? '/api/predict/logic' : '/api/predict/ml';
  let payload = { wavelengths: wvs };
  
  if (type === 'logic') {
    payload.logic_id = parseInt(methodId);
    try {
      payload.calibration_data = JSON.parse(document.getElementById('calibration-data-input').value);
    } catch(e) {
      alert("Invalid calibration JSON"); return;
    }
  } else {
    payload.model_id = methodId;
  }

  const runBtn = document.getElementById('run-btn');
  runBtn.innerHTML = 'Running...'; runBtn.disabled = true;

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    
    switchTab('results');
    
    if (data.error) {
      document.getElementById('main-result').className = 'alert alert-error';
      document.getElementById('main-result').innerHTML = `<strong>Error:</strong> ${data.error}`;
      if(data.missing) {
         document.getElementById('main-result').innerHTML += `<br>Missing Features: ${data.missing.join(', ')}`;
      }
    } else {
      document.getElementById('main-result').className = 'alert alert-success';
      document.getElementById('main-result').innerHTML = `
        <strong>Target:</strong> ${target} <br>
        <strong>Predicted Value:</strong> ${data.prediction.toFixed(4)} <br>
        <strong>Method Type:</strong> ${type === 'logic' ? 'Mathematical Logic' : 'ML Model'} <br>
        <strong>Method:</strong> ${methodId}
      `;
      addToHistory(target, type, methodId, data.prediction);
    }
  } catch (e) {
    alert("Request failed: " + e);
  } finally {
    runBtn.innerHTML = 'Run Prediction'; runBtn.disabled = false;
  }
}

function addToHistory(target, type, name, pred) {
  const tbody = document.getElementById('history-tbody');
  const date = new Date().toLocaleString();
  tbody.innerHTML = `<tr>
    <td>${date}</td>
    <td>${target}</td>
    <td>${type}</td>
    <td>${name}</td>
    <td>${pred.toFixed(4)}</td>
  </tr>` + tbody.innerHTML;
}

async function refreshModels() {
  const list = document.getElementById('models-list');
  list.innerHTML = 'Loading...';
  const res = await fetch('/api/ml/refresh', { method: 'POST' });
  const data = await res.json();
  
  let html = '<h4>Valid Models</h4><ul>';
  data.valid.forEach(m => {
    html += `<li>✓ ${m.id} (Target: ${m.target}, Type: ${m.type}, Features: ${m.features.length})</li>`;
  });
  html += '</ul><h4>Invalid Models</h4><ul>';
  data.invalid.forEach(m => {
    html += `<li style="color:red">✗ ${m.id} - ${m.error}</li>`;
  });
  html += '</ul>';
  list.innerHTML = html;
}

init();
async function trainModel() {
  document.getElementById(btn-train).innerHTML = Training...;
  document.getElementById(btn-train).disabled = true;
  const target = document.getElementById(train-target).value;
  const algo = document.getElementById(train-algo).value;
  try {
    const res = await fetch(/api/ml/train, {
      method: POST,
      headers: { Content-Type: application/json },
      body: JSON.stringify({ target, algo })
    });
    const data = await res.json();
    if (data.status === success) {
      document.getElementById(train-results).style.display = block;
      document.getElementById(train-metrics).innerHTML = Model saved:  + data.model_saved + <br>MAE:  + data.metrics.MAE + , MSE:  + data.metrics.MSE + , RMSE:  + data.metrics.RMSE + , R2:  + data.metrics.R2;
    }
  } catch (e) { alert(Training failed); }
  document.getElementById(btn-train).innerHTML = Train Model;
  document.getElementById(btn-train).disabled = false;
}
