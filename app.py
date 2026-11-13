import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import glob
import importlib.util
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from logics.common.nutrient_rules import soft_clamp, THRESHOLDS, get_nutrient_status, get_documented_limits, clamp

app = Flask(__name__, static_folder="frontend/dist", static_url_path="/")
CORS(app)

# ── Scispectrum research mode ────────────────────────────────────────────────
# SCISPECTRUM_RESEARCH_MODE=1 → analysis-only deployment for researchers on the
# ArkaShine site (/research). Anything that changes models, logics or calibration
# on the server is refused.
RESEARCH_MODE = os.environ.get("SCISPECTRUM_RESEARCH_MODE", "0") == "1"
BLOCKED_IN_RESEARCH = {
    ("POST", "/api/calibration/upload"),
    ("POST", "/api/calibration/save"),
    ("POST", "/api/logics"),
    ("POST", "/api/models/train"),
    ("POST", "/api/models/test"),
}


@app.before_request
def _research_guard():
    if RESEARCH_MODE and (request.method, request.path.rstrip("/")) in BLOCKED_IN_RESEARCH:
        return jsonify({"error": "This action is disabled in the Scispectrum research edition."}), 403

LOGICS_DEF_DIR   = PROJECT_ROOT / "logics" / "definitions"
LOGICS_IMPL_DIR  = PROJECT_ROOT / "logics" / "implementations"
CALIBRATION_DIR  = PROJECT_ROOT / "calibration"
CALIBRATION_FILE = CALIBRATION_DIR / "calibration.json"
MODELS_DIR       = PROJECT_ROOT / "models"
DB_PATH          = PROJECT_ROOT / "history.db"

for d in [LOGICS_DEF_DIR, LOGICS_IMPL_DIR, CALIBRATION_DIR, MODELS_DIR]:
    os.makedirs(d, exist_ok=True)

# Updated to exactly match physical hardware's alphabetical sensor_output order
# [A, B, C, D, E, F, G, H, I, J, K, L, R, S, T, U, V, W, UVA, UVB, UVC]
WAVELENGTH_ORDER = [410,435,460,485,510,535,560,585,645,705,900,940,610,680,730,760,810,860,320,280,200]
FEATURE_NAMES    = ["nm_" + str(nm) for nm in WAVELENGTH_ORDER]
ALL_TARGETS      = ["OC","N","P","K","Ca","Mg","S","Fe","Mn","Cu","Zn","B"]


# ──────────────────────────────────────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS predictions")
    c.execute("DROP TABLE IF EXISTS runs")
    c.execute(
        "CREATE TABLE runs ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "run_id TEXT UNIQUE,"
        "mode TEXT,"
        "date TEXT,"
        "time TEXT,"
        "timestamp REAL,"
        "samples INTEGER,"
        "nutrients INTEGER,"
        "calibration_file TEXT"
        ")"
    )
    c.execute(
        "CREATE TABLE predictions ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "run_id TEXT,"
        "sample_id TEXT,"
        "nutrient TEXT,"
        "selected_method TEXT,"
        "executed_method TEXT,"
        "method_type TEXT,"
        "calib_required INTEGER,"
        "calib_source TEXT,"
        "wavelengths_used TEXT,"
        "raw_pred REAL,"
        "clamp_applied INTEGER,"
        "clamp_rule TEXT,"
        "final_pred REAL,"
        "actual REAL,"
        "error REAL,"
        "status TEXT,"
        "FOREIGN KEY(run_id) REFERENCES runs(run_id)"
        ")"
    )
    conn.commit()
    conn.close()


if not os.path.exists(DB_PATH):
    init_db()
else:
    _conn = sqlite3.connect(DB_PATH)
    _c = _conn.cursor()
    _c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='runs'")
    _has_runs = _c.fetchone()
    _conn.close()
    if not _has_runs:
        init_db()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ──────────────────────────────────────────────────────────────────────────────
# CALIBRATION APIs
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/calibration", methods=["GET"])
def get_calibration():
    if not os.path.exists(CALIBRATION_FILE):
        return jsonify({"status": "NOT_FOUND", "message": "No calibration file uploaded."}), 404
    try:
        with open(CALIBRATION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        available = [t for t in ALL_TARGETS if t in data]
        return jsonify({"status": "VALID", "filename": "calibration.json",
                        "nutrients_available": len(available), "nutrients": available, "data": data})
    except Exception as e:
        return jsonify({"status": "INVALID", "message": str(e)}), 400


@app.route("/api/calibration/upload", methods=["POST"])
def upload_calibration():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    try:
        raw  = file.read()
        data = json.loads(raw)
        with open(CALIBRATION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        available = [t for t in ALL_TARGETS if t in data]
        return jsonify({"success": True, "nutrients_available": len(available), "nutrients": available})
    except Exception as e:
        return jsonify({"error": "Invalid JSON: " + str(e)}), 400


@app.route("/api/calibration/save", methods=["POST"])
def save_calibration():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        with open(CALIBRATION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        available = [t for t in ALL_TARGETS if t in data]
        return jsonify({"success": True, "nutrients_available": len(available), "nutrients": available})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ──────────────────────────────────────────────────────────────────────────────
# LOGIC & MODEL REGISTRY APIs
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/logics", methods=["GET"])
def get_logics():
    logics = []
    for f in glob.glob(os.path.join(LOGICS_DEF_DIR, "*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                d = json.load(fh)
            # Normalize: support both 'id' and 'logic_id' key names
            logic_id = d.get("id") or d.get("logic_id") or os.path.splitext(os.path.basename(f))[0]
            d["id"] = logic_id
            d["name"] = d.get("name") or d.get("logic_name") or logic_id
            impl_path = os.path.join(LOGICS_IMPL_DIR, logic_id + ".py")
            d["status"] = "Implemented" if os.path.exists(impl_path) else "NOT IMPLEMENTED"
            logics.append(d)
        except Exception:
            pass
    logics.sort(key=lambda x: x.get("id", ""))
    return jsonify(logics)


@app.route("/api/logics/<logic_id>", methods=["GET"])
def get_logic_detail(logic_id):
    def_path  = os.path.join(LOGICS_DEF_DIR,  logic_id + ".json")
    impl_path = os.path.join(LOGICS_IMPL_DIR, logic_id + ".py")
    if not os.path.exists(def_path):
        return jsonify({"error": "Logic not found"}), 404
    with open(def_path, "r", encoding="utf-8") as f:
        definition = json.load(f)
    impl_code = ""
    if os.path.exists(impl_path):
        with open(impl_path, "r", encoding="utf-8") as f:
            impl_code = f.read()
    definition["status"] = "Implemented" if impl_code else "NOT IMPLEMENTED"
    return jsonify({"definition": definition, "implementation": impl_code})

@app.route("/api/logics", methods=["POST"])
def save_logic():
    data = request.json
    logic_id = data.get("id") or data.get("logic_id")
    if not logic_id:
        return jsonify({"error": "Logic ID is required"}), 400
        
    def_path  = os.path.join(LOGICS_DEF_DIR, logic_id + ".json")
    impl_path = os.path.join(LOGICS_IMPL_DIR, logic_id + ".py")
    
    definition = data.get("definition", {})
    impl_code = data.get("implementation", "")
    
    # Ensure ID is in definition
    definition["id"] = logic_id
    
    with open(def_path, "w", encoding="utf-8") as f:
        json.dump(definition, f, indent=4)
        
    if impl_code:
        with open(impl_path, "w", encoding="utf-8") as f:
            f.write(impl_code)
            
    return jsonify({"success": True})


@app.route("/api/models", methods=["GET"])
def get_models():
    methods = set()
    if os.path.exists(MODELS_DIR):
        for entry in os.scandir(MODELS_DIR):
            if entry.is_dir() and not entry.name.startswith('.'):
                methods.add(entry.name)
    
    models = []
    for m in sorted(list(methods)):
        models.append({"id": m, "name": m, "type": "ML Model"})
    return jsonify(models)


@app.route("/api/targets", methods=["GET"])
def get_targets():
    return jsonify(ALL_TARGETS)


# ──────────────────────────────────────────────────────────────────────────────
# CORE PREDICTION ENGINE
# ──────────────────────────────────────────────────────────────────────────────

def extract_wavelengths(sample_data):
    wvs = []
    for nm in WAVELENGTH_ORDER:
        val = sample_data.get("nm_" + str(nm), sample_data.get(str(nm), sample_data.get(nm, 0)))
        try:
            v = float(val)
            if v != v:  # NaN
                v = 0.0
        except (TypeError, ValueError):
            v = 0.0
        wvs.append(v)
    return wvs


def extract_actual(sample_data, target):
    for key in sample_data.keys():
        k = str(key).strip().lower()
        t = str(target).strip().lower()
        if k == t or k.startswith(t + "%") or k.startswith(t + " ") or k.startswith(t + "_") or k.startswith(t + "("):
            val = sample_data.get(key)
            if val is not None and str(val).strip() not in ("", "nan", "NaN", "None"):
                try:
                    return float(val)
                except (TypeError, ValueError):
                    pass
    return None


def calc_fod_inference(X, alpha=0.5, K=5):
    w = np.zeros(K)
    w[0] = 1.0
    for k in range(1, K):
        w[k] = w[k-1] * (k - 1 - alpha) / k
    w = (-1) ** np.arange(K) * w
    out = np.zeros_like(X)
    for i in range(len(X)):
        for t in range(X.shape[1]):
            val = 0.0
            for k in range(min(t + 1, K)):
                val += w[k] * X[i, t - k]
            out[i, t] = val
    return out

def calc_msc_inference(X, ref):
    X_c = np.zeros_like(X)
    for i in range(len(X)):
        p = np.polyfit(ref, X[i], 1)
        slope = p[0] if abs(p[0]) > 1e-5 else 1.0
        X_c[i] = (X[i] - p[1]) / slope
    return X_c

def calc_ndsi_features_inference(X, top_k_indices):
    N = X.shape[0]
    mat = np.zeros((N, len(top_k_indices)))
    for idx, (i, j) in enumerate(top_k_indices):
        mat[:, idx] = (X[:, i] - X[:, j]) / (X[:, i] + X[:, j] + 1e-6)
    return np.hstack([X, mat])

def execute_prediction(sample_data, target, method_type, method_id, is_cal_required):
    wvs    = extract_wavelengths(sample_data)
    actual = extract_actual(sample_data, target)

    # ── ML path ──────────────────────────────────────────────────────────────
    if method_type == "ml":
        # Determine target prefixes based on the two naming conventions
        target_clean_1 = target.split(' ')[0].replace('%', '')
        TARGET_CLEAN_MAP = {
            'OC%': 'OC', 'N Kg/ha': 'N', 'P2O5': 'P', 'K2O': 'K', 'Ca (meq)': 'Ca',
            'Mg (meq)': 'Mg', 'SO4': 'S', 'Fe (ppm)': 'Fe', 'Mn (ppm)': 'Mn',
            'Cu (ppm)': 'Cu', 'Zn (ppm)': 'Zn', 'B (ppm)': 'B'
        }
        target_clean_2 = TARGET_CLEAN_MAP.get(target, target_clean_1)

        if method_id.endswith(".pkl"):
            # Backward compatibility (e.g., benchmark script passing full path)
            m_path = os.path.join(MODELS_DIR, method_id)
        else:
            # Look for the correct file inside the selected model folder
            base_dir = os.path.join(MODELS_DIR, method_id)
            m_path_1 = os.path.join(base_dir, f"{target_clean_1}_model.pkl")
            m_path_2 = os.path.join(base_dir, f"{target_clean_2}_model.pkl")
            
            if os.path.exists(m_path_1):
                m_path = m_path_1
            elif os.path.exists(m_path_2):
                m_path = m_path_2
            else:
                matches = glob.glob(os.path.join(base_dir, f"{target_clean_1}*.pkl")) + \
                          glob.glob(os.path.join(base_dir, f"{target_clean_2}*.pkl"))
                if matches:
                    m_path = matches[0]
                else:
                    raise Exception(f"ML Model file for nutrient '{target}' not found in: {method_id}")

        if not os.path.exists(m_path):
            raise Exception("ML Model file not found: " + str(m_path))

        model_payload = joblib.load(m_path)
        features_used = FEATURE_NAMES

        # Normalize bundle structure (some wrap inside {"model": ...}, some save the dict directly)
        if isinstance(model_payload, dict) and "model" in model_payload:
            m_obj = model_payload["model"]
        else:
            m_obj = model_payload

        if isinstance(m_obj, dict):
            if "classifier" in m_obj and "regressors" in m_obj:
                is_two_stage = True
                scaler     = m_obj["scaler"]
                classifier = m_obj["classifier"]
                regressors = m_obj["regressors"]
                features   = model_payload.get("features", FEATURE_NAMES)
                features_used = list(features)
                input_df   = pd.DataFrame([wvs], columns=FEATURE_NAMES)[features_used]
                X_scaled   = scaler.transform(input_df.values)
                pred_class = classifier.predict(X_scaled)[0]
                reg        = regressors.get(pred_class)
                if reg is None:
                    raise Exception("No regressor found for class: " + str(pred_class))
                
                if isinstance(reg, tuple):
                    reg = reg[1]
                    
                raw_pred = float(reg.predict(X_scaled)[0])
                
                is_clamped = False
                clamp_rule = "None"
                
                rules = m_obj.get("rules", {})
                if rules and pred_class in rules:
                    lo, hi = rules[pred_class]
                    pred = float(soft_clamp(raw_pred, lo, hi, pred_class, target))
                    if pred != raw_pred:
                        is_clamped = True
                        clamp_rule = f"Soft clamp applied for class '{pred_class}' using model rules"
                else:
                    pred = raw_pred
                    
                final_pred = pred
            elif isinstance(m_obj, dict) and "class_scalers" in m_obj:
                # Frozen Two-Stage
                sc_clf = m_obj["sc_clf"]
                clf = m_obj["clf"]
                sc_reg = m_obj["sc_reg"]
                reg = m_obj["reg"]
                class_scalers = m_obj["class_scalers"]
                active_rules = m_obj["active_rules"]
                
                features = model_payload.get("features", FEATURE_NAMES)
                features_used = list(features)
                input_df = pd.DataFrame([wvs], columns=FEATURE_NAMES)[features_used]
                
                X_c = sc_clf.transform(input_df.values)
                X_r = sc_reg.transform(input_df.values)
                
                if clf is not None:
                    pred_class = clf.predict(X_c)[0]
                else:
                    pred_class = m_obj["fallback_class"]
                    
                raw_pred = float(np.maximum(0, reg.predict(X_r).flatten()[0]))
                
                is_clamped = False
                clamp_rule = "None"
                
                if pred_class in active_rules:
                    low_b, high_b = active_rules[pred_class]
                    midpoint = (low_b + high_b) / 2.0
                    blended_val = (raw_pred + midpoint) / 2.0
                    scaler = class_scalers.get(pred_class)
                    
                    if scaler is not None:
                        pred = float(scaler.transform([[blended_val]])[0][0])
                    else:
                        pred = blended_val
                        
                    pred = float(np.clip(pred, low_b, high_b))
                    if pred != raw_pred:
                        is_clamped = True
                        clamp_rule = f"Blended bounding applied for [{low_b}, {high_b}]"
                else:
                    pred = raw_pred
                    
                final_pred = pred
            elif isinstance(m_obj, dict) and m_obj.get("type") == "advanced_ensemble":
                preproc_type = m_obj.get("preproc_type", "standard")
                scaler_c = m_obj["scaler_classifier"]
                clf = m_obj["classifier"]
                scaler_r = m_obj["scaler_regressor"]
                models = m_obj["models"] # dict of regressors
                weights = m_obj.get("weights", []) # list of weights
                rules = m_obj.get("rules", {})
                
                features = model_payload.get("features", FEATURE_NAMES)
                features_used = list(features)
                input_df = pd.DataFrame([wvs], columns=FEATURE_NAMES)[features_used]
                X_base = input_df.values
                
                if preproc_type == "ndsi":
                    X_base = calc_ndsi_features_inference(X_base, m_obj.get("ndsi_top_k", []))
                elif preproc_type == "fod":
                    X_base = calc_fod_inference(X_base, alpha=0.5)
                    
                X_c = scaler_c.transform(X_base)
                pred_class = clf.predict(X_c)[0]
                
                if preproc_type == "msc":
                    X_msc = calc_msc_inference(X_base, m_obj.get("msc_ref", np.zeros(X_base.shape[1])))
                    X_r = scaler_r.transform(X_msc)
                else:
                    X_r = scaler_r.transform(X_base)
                    
                if isinstance(models, dict) and weights:
                    # It's an ensemble
                    p_raw = 0.0
                    for (mod_name, mod_obj), w in zip(models.items(), weights):
                        pred_out = mod_obj.predict(X_r)
                        if hasattr(pred_out, "ravel"):
                            pred_out = pred_out.ravel()[0]
                        elif isinstance(pred_out, (list, np.ndarray)):
                            pred_out = pred_out[0]
                        p_raw += w * pred_out
                else:
                    # Single regressor
                    if isinstance(models, dict): models = list(models.values())[0]
                    p_out = models.predict(X_r)
                    if hasattr(p_out, "ravel"): p_out = p_out.ravel()[0]
                    elif isinstance(p_out, (list, np.ndarray)): p_out = p_out[0]
                    p_raw = float(p_out)
                    
                p_raw = float(max(0.0, p_raw))
                is_clamped = False
                clamp_rule = "None"
                
                if pred_class in rules:
                    low_b, high_b = rules[pred_class]
                    span = high_b - low_b
                    b_min = max(0.0, low_b - 0.10 * span)
                    b_max = high_b + 0.10 * span
                    final_p = np.clip(p_raw, b_min, b_max)
                    if final_p != p_raw:
                        is_clamped = True
                        clamp_rule = f"Clamped to {pred_class} bounds (+/- 10%)"
                else:
                    agronomic_min = m_obj.get("agronomic_min", 0.0)
                    agronomic_max = m_obj.get("agronomic_max", 9999.0)
                    final_p = np.clip(p_raw, agronomic_min, agronomic_max)
                raw_pred = p_raw
                final_pred = float(final_p)
            else:
                # Unified model packed in a dict
                scaler = model_payload.get("scaler")
                reg = m_obj
                features = model_payload.get("features", getattr(reg, "feature_names_in_", FEATURE_NAMES))
                if features is None or isinstance(features, int) or (len(features) > 0 and str(features[0]).startswith("Column_")):
                    features = FEATURE_NAMES
                features_used = list(features)
                
                # Safe dataframe column selection
                valid_features = [f for f in features_used if f in FEATURE_NAMES]
                if not valid_features:
                    valid_features = FEATURE_NAMES
                
                input_df = pd.DataFrame([wvs], columns=FEATURE_NAMES)[valid_features]
                
                if scaler:
                    X_input = scaler.transform(input_df.values)
                else:
                    X_input = input_df.values
                    
                raw_pred = float(reg.predict(X_input)[0])
                min_limit, max_limit, is_clamped, _ = get_documented_limits("ml", method_id)
                final_pred = clamp(raw_pred, min_limit, max_limit) if (is_clamped and min_limit is not None and max_limit is not None) else raw_pred
                clamp_rule = "[" + str(min_limit) + ", " + str(max_limit) + "]" if is_clamped else "None"
                pred_class = get_nutrient_status(target, final_pred)
                
        else:
            features = getattr(model_payload, "feature_names_in_", None)
            if features is None or isinstance(features, int) or (len(features) > 0 and str(features[0]).startswith("Column_")):
                features = FEATURE_NAMES
            features_used = list(features)
            
            valid_features = [f for f in features_used if f in FEATURE_NAMES]
            if not valid_features:
                valid_features = FEATURE_NAMES
                
            input_df = pd.DataFrame([wvs], columns=FEATURE_NAMES)
            
            if set(valid_features).issubset(set(FEATURE_NAMES)):
                raw_pred = float(model_payload.predict(input_df[valid_features].values)[0])
            else:
                raw_pred = float(model_payload.predict(input_df.values)[0])
                
            min_limit, max_limit, is_clamped, _ = get_documented_limits("ml", method_id)
            final_pred = clamp(raw_pred, min_limit, max_limit) if (is_clamped and min_limit is not None and max_limit is not None) else raw_pred
            clamp_rule = "[" + str(min_limit) + ", " + str(max_limit) + "]" if is_clamped else "None"
            pred_class = get_nutrient_status(target, final_pred)

        return {
            "nutrient": target, 
            "selected_method": method_id, 
            "executed_method": method_id,
            "method_type": "ML Model", 
            "calibration_required": False,
            "calibration_used": False,
            "calibration_source": "Not Required (ML)", 
            "wavelengths_used": features_used,
            "raw_prediction": raw_pred, 
            "clamp_applied": is_clamped,
            "clamp_rule": clamp_rule,
            "final_prediction": final_pred, 
            "actual": actual,
            "error": round(final_pred - actual, 4) if actual is not None else None,
            "status": get_nutrient_status(target, final_pred),
            "predicted_class": str(pred_class) if 'pred_class' in locals() else get_nutrient_status(target, final_pred),
            "actual_class": get_nutrient_status(target, actual) if actual is not None else "UNKNOWN"
        }

    # ── Logic path ───────────────────────────────────────────────────────────
    elif method_type == "logic":
        def_path = os.path.join(LOGICS_DEF_DIR, method_id + ".json")
        if not os.path.exists(def_path):
            raise Exception("Logic definition not found: " + method_id + ".json")
        with open(def_path, "r", encoding="utf-8") as fh:
            logic_def = json.load(fh)

        impl_path = os.path.join(LOGICS_IMPL_DIR, method_id + ".py")
        if not os.path.exists(impl_path):
            raise Exception(method_id + " is NOT IMPLEMENTED. Cannot execute.")

        # AUTOMATIC CALIBRATION RULE
        is_cal_required = logic_def.get("calibration_required", False)

        cal_data   = None
        cal_source = "Not Required"

        if is_cal_required:
            if not os.path.exists(CALIBRATION_FILE):
                return {
                    "nutrient": target, "selected_method": method_id, "executed_method": method_id, "method_type": "Logic",
                    "calibration_required": True, "calibration_used": False, "calibration_source": "Missing calibration.json",
                    "wavelengths_used": [], "required_ips": [], "raw_prediction": None, "clamp_applied": False,
                    "clamp_rule": "None", "final_prediction": None, "actual": actual, "error": None,
                    "status": "INCOMPLETE / DOCUMENTATION REQUIRED",
                    "detailed_steps": {"error": "INCOMPLETE: Calibration required but calibration.json is missing. Cannot calculate."}
                }
            with open(CALIBRATION_FILE, "r", encoding="utf-8") as cf:
                all_cals = json.load(cf)
            if target not in all_cals:
                return {
                    "nutrient": target, "selected_method": method_id, "executed_method": method_id, "method_type": "Logic",
                    "calibration_required": True, "calibration_used": False, "calibration_source": "Not Found in calibration.json",
                    "wavelengths_used": [], "required_ips": [], "raw_prediction": None, "clamp_applied": False,
                    "clamp_rule": "None", "final_prediction": None, "actual": actual, "error": None,
                    "status": "INCOMPLETE / DOCUMENTATION REQUIRED",
                    "detailed_steps": {"error": f"INCOMPLETE: No calibration data found for {target} in calibration.json. Cannot execute securely."}
                }
            # Load THIS nutrient's section ONLY — never another nutrient's
            cal_data = all_cals[target]
            if "vals" not in cal_data:
                cal_data["vals"] = [
                    cal_data.get("value_min", 0),
                    cal_data.get("value_mid", 0),
                    cal_data.get("value_max", 0)
                ]
            cal_source = "calibration.json [" + target + "]"

        spec = importlib.util.spec_from_file_location(method_id, impl_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        try:
            res = mod.predict(wvs, cal_data, target)
        except TypeError:
            res = mod.predict(wvs, cal_data)
            
        details = {}
        features_override = None
        if isinstance(res, dict):
            raw_pred = float(res.get("value", 0.0))
            details = res.get("details", {})
            features_override = res.get("features_used", None)
        elif isinstance(res, tuple):
            raw_pred = float(res[0])
            details = res[1] if len(res) > 1 else {}
        else:
            raw_pred = float(res)

        # Get the documentation limits, but prioritize any override from the logic details
        min_limit, max_limit, is_clamped, _ = get_documented_limits("logic", method_id, target)
        
        if "bounds" in details:
            min_limit, max_limit = details["bounds"]
            is_clamped = True

        if "error" in details:
            return {
                "nutrient": target, 
                "selected_method": method_id, 
                "executed_method": method_id,
                "method_type": "Logic", 
                "calibration_required": logic_def.get("calibration_required", False),
                "calibration_used": bool(is_cal_required),
                "calibration_source": cal_source, 
                "wavelengths_used": features_override if features_override is not None else logic_def.get("features", FEATURE_NAMES),
                "required_ips": logic_def.get("required_ips", []),
                "raw_prediction": None, 
                "clamp_applied": False,
                "clamp_rule": "None",
                "final_prediction": None, 
                "actual": actual,
                "error": None,
                "status": "INCOMPLETE / DOCUMENTATION REQUIRED",
                "detailed_steps": details
            }

        final_pred = clamp(raw_pred, min_limit, max_limit) if (is_clamped and min_limit is not None and max_limit is not None) else raw_pred
        features_used = features_override if features_override is not None else logic_def.get("features", FEATURE_NAMES)

        return {
            "nutrient": target, 
            "selected_method": method_id, 
            "executed_method": method_id,
            "method_type": "Logic", 
            "calibration_required": logic_def.get("calibration_required", False),
            "calibration_used": bool(is_cal_required),
            "calibration_source": cal_source, 
            "wavelengths_used": features_used,
            "required_ips": logic_def.get("required_ips", []),
            "raw_prediction": raw_pred, 
            "clamp_applied": bool(is_clamped),
            "clamp_rule": "[" + str(min_limit) + ", " + str(max_limit) + "]" if is_clamped else "None",
            "final_prediction": final_pred, 
            "actual": actual,
            "error": round(final_pred - actual, 4) if actual is not None else None,
            "status": get_nutrient_status(target, final_pred),
            "predicted_class": get_nutrient_status(target, final_pred),
            "actual_class": get_nutrient_status(target, actual) if actual is not None else "UNKNOWN",
            "detailed_steps": details
        }
    else:
        raise Exception("Unknown method type: " + str(method_type))


def process_request(mode, data):
    run_id  = "RUN-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6].upper()
    samples = data.get("samples", [])
    targets = data.get("targets", [])
    mapping = data.get("mapping", {})
    results = []

    # NUTRIENT-WISE EXECUTION: Process nutrient by nutrient across all samples
    for t in targets:
        conf = mapping.get(t)
        if not conf:
            continue
            
        selected_m = conf.get("method_id", "Unknown")
        m_type     = conf.get("method_type", "Unknown")
        cal_req    = conf.get("calibration_required", False)

        for s in samples:
            s_id = s.get("Sample_ID", "Unknown")
            try:
                res = execute_prediction(
                    sample_data    = s,
                    target         = t,
                    method_type    = m_type,
                    method_id      = selected_m,
                    is_cal_required= cal_req
                )
                
                # MANDATORY ASSERTION
                assert res["selected_method"] == res["executed_method"], (
                    f"Method mismatch: Selected={res['selected_method']} vs Executed={res['executed_method']}"
                )
                
                if res["raw_prediction"] == 0.0 or res["final_prediction"] == 0.0:
                    print(f"[ZERO PREDICTION WARNING] {s_id} | {t} | Selected={res['selected_method']} | Executed={res['executed_method']} | Raw={res['raw_prediction']} | Final={res['final_prediction']}")

            except Exception as e:
                res = {
                    "nutrient": t,
                    "selected_method": selected_m,
                    "executed_method": "ERROR",
                    "method_type": m_type,
                    "calibration_required": cal_req,
                    "calibration_source": "ERROR",
                    "wavelengths_used": [],
                    "raw_prediction": None,
                    "clamp_applied": False,
                    "clamp_rule": "N/A",
                    "final_prediction": None,
                    "actual": None,
                    "error": None,
                    "status": "FAILED: " + str(e)
                }
            res["sample_id"] = s_id
            results.append(res)
            
            p_val = f"{res['final_prediction']:.4f}" if res['final_prediction'] is not None else ("INCOMPLETE" if "INCOMPLETE" in res['status'] else "ERROR")
            print(f"Sample: {s_id:<12} | Nutrient: {t:<4} | Selected={res['selected_method']:<10} | Executed={res['executed_method']:<10} | Pred={p_val}")

    now  = datetime.now()
    conn = get_db()
    c    = conn.cursor()
    c.execute(
        "INSERT INTO runs (run_id,mode,date,time,timestamp,samples,nutrients,calibration_file) VALUES (?,?,?,?,?,?,?,?)",
        (run_id, mode, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
         time.time(), len(samples), len(targets), "calibration.json")
    )
    INSERT_SQL = (
        "INSERT INTO predictions (run_id,sample_id,nutrient,selected_method,executed_method,"
        "method_type,calib_required,calib_source,wavelengths_used,raw_pred,clamp_applied,"
        "clamp_rule,final_pred,actual,error,status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    for r in results:
        c.execute(INSERT_SQL, (
            run_id, r.get("sample_id"), r.get("nutrient"), r.get("selected_method"),
            r.get("executed_method"), r.get("method_type"),
            1 if r.get("calibration_required") else 0,
            r.get("calibration_source"),
            json.dumps(r.get("wavelengths_used", [])),
            r.get("raw_prediction"), 1 if r.get("clamp_applied") else 0,
            r.get("clamp_rule"), r.get("final_prediction"),
            r.get("actual"), r.get("error"), r.get("status")
        ))
        conn.commit()
    conn.close()
    return jsonify({"success": True, "run_id": run_id, "results": results})


@app.route('/api/models/train', methods=['POST'])
def train_ml_models():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    file_path = os.path.join('data', 'data.xlsx')
    file.save(file_path)
    
    model_name = request.form.get('model_name')
    
    import subprocess
    try:
        if model_name and model_name.upper() != "ALL":
            if model_name == "Frozen_Optimal_Models":
                result = subprocess.run(['python', 'train_frozen_models.py'], capture_output=True, text=True)
            elif model_name.startswith("Combo_") or model_name.startswith("Model_2") or model_name.startswith("Model_3"):
                result = subprocess.run(['python', 'build_dashboard_advanced_models.py', model_name], capture_output=True, text=True)
            else:
                result = subprocess.run(['python', 'build_all_pdf_models_v2.py', model_name], capture_output=True, text=True)
                
            if result.returncode != 0:
                return jsonify({'error': f'{model_name} training failed', 'details': result.stderr}), 500
            return jsonify({'success': True, 'message': f'{model_name} trained successfully!'})
        else:
            # Train all models across all suites
            # 1. Advanced Ensembles (Combo_01 to Combo_30 & Suite 4 Models 28-37)
            res_adv = subprocess.run(['python', 'build_dashboard_advanced_models.py'], capture_output=True, text=True)
            if res_adv.returncode != 0:
                return jsonify({'error': 'Advanced combos training failed', 'details': res_adv.stderr}), 500

            # 2. Frozen optimal models
            res_frz = subprocess.run(['python', 'train_frozen_models.py'], capture_output=True, text=True)
            if res_frz.returncode != 0:
                return jsonify({'error': 'Frozen models training failed', 'details': res_frz.stderr}), 500
                
            # 3. Extended benchmark architectures
            res_ext = subprocess.run(['python', 'build_all_pdf_models_v2.py'], capture_output=True, text=True)
            if res_ext.returncode != 0:
                return jsonify({'error': 'Extended models training failed', 'details': res_ext.stderr}), 500
                
            return jsonify({'success': True, 'message': 'All 70+ ML models retrained successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/test', methods=['POST'])
def test_ml_model():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    model_name = request.form.get('model_name')
    
    if not model_name:
        return jsonify({'error': 'No model selected'}), 400
        
    df = pd.read_excel(file)
    df.fillna(0, inplace=True)
    samples = df.to_dict(orient="records")
    
    # Use all potential targets; extract_actual handles loose matching (e.g., 'OC' matches 'OC%')
    available_targets = ALL_TARGETS
    
    results = []
    for target in available_targets:
        for sample in samples:
            actual = extract_actual(sample, target)
            if actual is None: continue
            
            try:
                res = execute_prediction(
                    sample_data=sample,
                    target=target,
                    method_type="ml",
                    method_id=model_name,
                    is_cal_required=False
                )
                
                results.append({
                    "sample_id": sample.get("Sample_ID", "Unknown"),
                    "nutrient": target,
                    "actual": actual,
                    "predicted": res.get("final_prediction"),
                    "error": res.get("error")
                })
            except Exception as e:
                pass

    if not results:
        return jsonify({"error": "No valid targets/samples found to test"}), 400

    # Save to Excel with graphs
    import io
    report_dir = os.path.join(PROJECT_ROOT, "test_reports")
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"TestReport_{model_name}_{timestamp}.xlsx"
    filepath = os.path.join(report_dir, filename)
    
    df_res = pd.DataFrame(results)
    
    # Create Excel file using xlsxwriter
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
    
    # Write full raw results to a master sheet
    df_res.to_excel(writer, sheet_name='All Results', index=False)
    
    workbook = writer.book
    
    for nutrient in available_targets:
        nut_df = df_res[df_res['nutrient'] == nutrient]
        if nut_df.empty: continue
        
        # Sheet names have character limits and invalid chars
        sheet_name = nutrient.replace('/', '_').replace('%', 'pct')[:31]
        nut_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        worksheet = writer.sheets[sheet_name]
        
        # Create a scatter chart
        chart = workbook.add_chart({'type': 'scatter'})
        
        max_row = len(nut_df) + 1
        
        # columns in nut_df: sample_id(A), nutrient(B), actual(C), predicted(D), error(E)
        chart.add_series({
            'name':       f'{nutrient} Actual vs Predicted',
            'categories': [sheet_name, 1, 2, max_row - 1, 2], # Actual (Col C)
            'values':     [sheet_name, 1, 3, max_row - 1, 3], # Predicted (Col D)
            'marker':     {'type': 'circle', 'size': 5},
            'trendline':  {'type': 'linear', 'name': 'Ideal Trend'}
        })
        
        chart.set_title ({'name': f'{nutrient} - Actual vs Predicted'})
        chart.set_x_axis({'name': 'Actual Laboratory Value'})
        chart.set_y_axis({'name': 'Model Predicted Value'})
        chart.set_size({'width': 720, 'height': 480})
        
        # Insert the chart beside the data
        worksheet.insert_chart('G2', chart)
        
    writer.close()
                
    return jsonify({
        "success": True, 
        "results": results, 
        "report_path": filepath,
        "report_url": f"/api/download/report/{filename}"
    })

@app.route('/api/download/report/<filename>', methods=['GET'])
def download_report(filename):
    report_dir = os.path.join(PROJECT_ROOT, "test_reports")
    return send_from_directory(report_dir, filename, as_attachment=True)


@app.route('/api/models/multi-eval', methods=['POST'])
def multi_eval_models():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    df = pd.read_excel(file)
    df.fillna(0, inplace=True)
    samples = df.to_dict(orient="records")
    
    selected_targets_json = request.form.get('targets')
    selected_methods_json = request.form.get('methods')
    mode_selection = request.form.get('mode', 'all_ml')
    pass_threshold_pct = float(request.form.get('pass_threshold', 75.0))
    dataset_type = request.form.get('dataset_type', 'new_test') # 'trained_data' or 'new_test'
    
    import json as pyjson
    targets_requested = pyjson.loads(selected_targets_json) if selected_targets_json else []
    methods_requested = pyjson.loads(selected_methods_json) if selected_methods_json else []
    
    if not targets_requested or "ALL" in targets_requested:
        eval_targets = [t for t in ALL_TARGETS if any(extract_actual(samples[0], t) is not None for _ in [1])]
        if not eval_targets:
            eval_targets = ALL_TARGETS
    else:
        eval_targets = targets_requested
        
    eval_methods = []
    if mode_selection == 'all_ml':
        if os.path.exists(MODELS_DIR):
            for entry in os.scandir(MODELS_DIR):
                if entry.is_dir() and not entry.name.startswith('.'):
                    eval_methods.append({"id": entry.name, "type": "ml", "name": entry.name})
    elif mode_selection == 'all_logic':
        for f in glob.glob(os.path.join(LOGICS_DEF_DIR, "*.json")):
            lid = os.path.splitext(os.path.basename(f))[0]
            eval_methods.append({"id": lid, "type": "logic", "name": lid})
    else:
        for m in methods_requested:
            eval_methods.append(m)
            
    if not eval_methods:
        return jsonify({'error': 'No models or mathematical logics selected'}), 400
        
    results = []
    method_metrics = {}
    
    for method in eval_methods:
        m_id = method["id"]
        m_type = method["type"]
        m_name = method.get("name", m_id)
        
        for target in eval_targets:
            key = (m_id, target)
            method_metrics[key] = {
                "method_id": m_id,
                "method_name": m_name,
                "method_type": m_type,
                "nutrient": target,
                "total_samples": 0,
                "passed_samples": 0,
                "total_abs_error": 0.0,
                "total_pct_error": 0.0,
                "preds": [],
                "actuals": [],
                "errors": []
            }
            
            for s_idx, sample in enumerate(samples):
                actual = extract_actual(sample, target)
                if actual is None:
                    continue
                    
                s_id = sample.get("Sample_ID", f"Sample_{s_idx+1}")
                try:
                    res = execute_prediction(
                        sample_data=sample,
                        target=target,
                        method_type=m_type,
                        method_id=m_id,
                        is_cal_required=True if m_type == 'logic' else False
                    )
                    pred = res.get("final_prediction")
                    if pred is None:
                        continue
                        
                    err = pred - actual
                    denom = abs(actual) if abs(actual) > 1e-4 else 1.0
                    err_pct = (abs(err) / denom) * 100.0
                    sample_acc = max(0.0, 100.0 - err_pct)
                    passed = (sample_acc >= pass_threshold_pct)
                    
                    method_metrics[key]["total_samples"] += 1
                    if passed:
                        method_metrics[key]["passed_samples"] += 1
                    method_metrics[key]["total_abs_error"] += abs(err)
                    method_metrics[key]["total_pct_error"] += err_pct
                    method_metrics[key]["preds"].append(pred)
                    method_metrics[key]["actuals"].append(actual)
                    method_metrics[key]["errors"].append(err)
                    
                    results.append({
                        "sample_id": s_id,
                        "nutrient": target,
                        "method_id": m_id,
                        "method_name": m_name,
                        "method_type": "Machine Learning" if m_type == 'ml' else "Mathematical Logic",
                        "actual": round(actual, 4),
                        "predicted": round(pred, 4),
                        "error": round(err, 4),
                        "accuracy_pct": round(sample_acc, 2),
                        "passed": passed
                    })
                except Exception as e:
                    pass

    summary = []
    for (m_id, target), stats in method_metrics.items():
        n = stats["total_samples"]
        if n > 0:
            pass_rate = (stats["passed_samples"] / n) * 100.0
            avg_acc = max(0.0, 100.0 - (stats["total_pct_error"] / n))
            mae = stats["total_abs_error"] / n
            summary.append({
                "method_id": m_id,
                "method_name": stats["method_name"],
                "method_type": "Machine Learning" if stats["method_type"] == 'ml' else "Mathematical Logic",
                "nutrient": target,
                "total_samples": n,
                "passed_samples": stats["passed_samples"],
                "pass_rate_pct": round(pass_rate, 2),
                "avg_accuracy_pct": round(avg_acc, 2),
                "mae": round(mae, 4)
            })
            
    # Sort primarily by nutrient, then arranged highest to lowest by accuracy
    summary.sort(key=lambda x: (x["nutrient"], -x["avg_accuracy_pct"], -x["pass_rate_pct"], x["mae"]))
    
    # Assign clear rank per nutrient (1 = highest accuracy)
    nut_counters = {}
    for item in summary:
        nut = item["nutrient"]
        r = nut_counters.get(nut, 0) + 1
        nut_counters[nut] = r
        item["nutrient_rank"] = r
    
    if not results:
        return jsonify({'error': 'No matching targets or predictions could be computed.'}), 400
        
    report_dir = os.path.join(PROJECT_ROOT, "test_reports")
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"MultiModel_Evaluation_{mode_selection}_{timestamp}.xlsx"
    filepath = os.path.join(report_dir, filename)
    
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
    workbook = writer.book
    
    # 1. Best Models Per Nutrient Sheet (Arranged with top accuracy per nutrient)
    best_per_nut = []
    seen_nuts = set()
    for item in summary:
        if item["nutrient"] not in seen_nuts:
            best_per_nut.append(item)
            seen_nuts.add(item["nutrient"])
    if best_per_nut:
        df_best = pd.DataFrame(best_per_nut)
        df_best.to_excel(writer, sheet_name='Best Models Per Nutrient', index=False)
        best_ws = writer.sheets['Best Models Per Nutrient']
        best_hdr_fmt = workbook.add_format({'bold': True, 'bg_color': '#10b981', 'font_color': 'white'})
        for col_idx, col_name in enumerate(df_best.columns):
            best_ws.write(0, col_idx, col_name, best_hdr_fmt)
            best_ws.set_column(col_idx, col_idx, 18)

    df_summary = pd.DataFrame(summary)
    df_summary.to_excel(writer, sheet_name='Summary Leaderboard', index=False)
    
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#0284c7', 'font_color': 'white'})
    summary_ws = writer.sheets['Summary Leaderboard']
    for col_idx, col_name in enumerate(df_summary.columns):
        summary_ws.write(0, col_idx, col_name, header_fmt)
        summary_ws.set_column(col_idx, col_idx, 18)
        
    df_res = pd.DataFrame(results)
    df_res.to_excel(writer, sheet_name='All Predictions', index=False)
    raw_ws = writer.sheets['All Predictions']
    for col_idx, col_name in enumerate(df_res.columns):
        raw_ws.write(0, col_idx, col_name, header_fmt)
        raw_ws.set_column(col_idx, col_idx, 16)
        
    for nutrient in eval_targets:
        nut_df = df_res[df_res['nutrient'] == nutrient]
        if nut_df.empty:
            continue
            
        sheet_name = f"Graph_{nutrient.replace('/', '_').replace('%', 'pct')}"[:31]
        nut_df.to_excel(writer, sheet_name=sheet_name, index=False)
        graph_ws = writer.sheets[sheet_name]
        
        chart = workbook.add_chart({'type': 'scatter'})
        max_r = min(len(nut_df) + 1, 300)
        
        chart.add_series({
            'name': f'{nutrient} - Actual vs Predicted',
            'categories': [sheet_name, 1, 5, max_r - 1, 5],
            'values':     [sheet_name, 1, 6, max_r - 1, 6],
            'marker':     {'type': 'circle', 'size': 5},
            'trendline':  {'type': 'linear', 'name': 'Ideal Trend'}
        })
        chart.set_title({'name': f'{nutrient}: Actual vs Predicted Comparison'})
        chart.set_x_axis({'name': 'Actual Value (Laboratory)'})
        chart.set_y_axis({'name': 'Predicted Value'})
        chart.set_size({'width': 750, 'height': 450})
        graph_ws.insert_chart('L2', chart)
        
    writer.close()
    
    # Build lightweight chart_data mapping: { "METHOD_ID::NUTRIENT": [ {x, y, sample_id, acc, passed} ] }
    chart_series_map = {}
    for (m_id, target), stats in method_metrics.items():
        if stats["total_samples"] > 0:
            k = f"{m_id}::{target}"
            points = []
            for pred_val, act_val in zip(stats["preds"], stats["actuals"]):
                err = pred_val - act_val
                denom = abs(act_val) if abs(act_val) > 1e-4 else 1.0
                err_pct = (abs(err) / denom) * 100.0
                sample_acc = max(0.0, 100.0 - err_pct)
                points.append({
                    "x": round(float(act_val), 4),
                    "y": round(float(pred_val), 4),
                    "acc": round(float(sample_acc), 2),
                    "passed": bool(sample_acc >= pass_threshold_pct)
                })
            chart_series_map[k] = points

    return jsonify({
        "success": True,
        "mode": mode_selection,
        "pass_threshold_pct": pass_threshold_pct,
        "dataset_type": dataset_type,
        "summary": summary,
        "chart_series_map": chart_series_map,
        "results": results[:500],
        "total_results_count": len(results),
        "report_url": f"/api/download/report/{filename}"
    })


@app.route("/api/benchmark", methods=["POST"])
def run_benchmark():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    df = pd.read_excel(file)
    df.fillna(0, inplace=True)
    samples = df.to_dict(orient="records")
    
    available_targets = [t for t in ALL_TARGETS if t in df.columns]
    if not available_targets:
        return jsonify({"error": "No valid target columns found in the uploaded file"}), 400
        
    with open(REGISTRY_FILE, "r") as f:
        logics = json.load(f)
    logic_ids = [k for k in logics.keys()]
    
    ml_models = []
    for f_path in glob.glob(os.path.join(MODELS_DIR, "**", "*.pkl"), recursive=True):
        ml_models.append(os.path.relpath(f_path, MODELS_DIR).replace("\\", "/"))
        
    all_methods = []
    for m in logic_ids:
        all_methods.append({"id": m, "type": "logic"})
    for m in ml_models:
        all_methods.append({"id": m, "type": "ml"})
        
    results_summary = {} 
    
    for target in available_targets:
        results_summary[target] = []
        for method in all_methods:
            if method["type"] == "ml":
                basename = os.path.basename(method["id"])
                target_clean = target.split(' ')[0].replace('%', '')
                # Basic check to skip mismatched models for speed
                if not basename.startswith(target_clean + "_"):
                    continue
                    
            correct = 0
            total_error = 0
            count = 0
            for sample in samples:
                actual = extract_actual(sample, target)
                if actual is None: continue
                
                try:
                    res = execute_prediction(
                        sample_data=sample,
                        target=target,
                        method_type=method["type"],
                        method_id=method["id"],
                        is_cal_required=False
                    )
                    pred_class = res.get("predicted_class") or res.get("status")
                    actual_class = res.get("actual_class")
                    if actual_class == "UNKNOWN" or not actual_class:
                        actual_class = get_nutrient_status(target, actual)
                        
                    if pred_class == actual_class:
                        correct += 1
                        
                    if res.get("final_prediction") is not None:
                        total_error += abs(res["final_prediction"] - actual)
                    count += 1
                except Exception as e:
                    pass
                    
            if count > 0:
                accuracy = (correct / count) * 100
                mae = total_error / count
                results_summary[target].append({
                    "method_id": method["id"],
                    "method_type": method["type"],
                    "accuracy": round(accuracy, 2),
                    "mae": round(mae, 4)
                })
                
        # Sort leaderboard by Accuracy DESC, then MAE ASC
        results_summary[target].sort(key=lambda x: (-x["accuracy"], x["mae"]))
        
    return jsonify({"success": True, "leaderboard": results_summary})

# ──────────────────────────────────────────────────────────────────────────────
# PREDICTION ROUTES
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/single/predict", methods=["POST"])
def predict_single():
    return process_request("MODE_2_SINGLE", request.json)


@app.route("/api/batch/predict", methods=["POST"])
def predict_batch():
    return process_request("MODE_1_BATCH", request.json)


@app.route("/api/all12/predict", methods=["POST"])
def predict_all12():
    return process_request("MODE_3_ALL12", request.json)


# ──────────────────────────────────────────────────────────────────────────────
# HISTORY ROUTES
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/runs", methods=["GET"])
def get_runs():
    conn = get_db()
    c    = conn.cursor()
    c.execute("SELECT * FROM runs ORDER BY id DESC")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/runs/<run_id>", methods=["GET"])
def get_run(run_id):
    conn = get_db()
    c    = conn.cursor()
    c.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
    run  = c.fetchone()
    if not run:
        conn.close()
        return jsonify({"error": "Run not found"}), 404
    c.execute("SELECT * FROM predictions WHERE run_id = ?", (run_id,))
    preds = [dict(row) for row in c.fetchall()]
    for p in preds:
        try:
            p["wavelengths_used"] = json.loads(p["wavelengths_used"])
        except Exception:
            pass
    conn.close()
    return jsonify({"run": dict(run), "predictions": preds})


@app.route("/api/history", methods=["GET"])
def get_history():
    conn = get_db()
    c    = conn.cursor()
    c.execute(
        "SELECT r.date, r.time, r.mode, p.* FROM predictions p "
        "JOIN runs r ON p.run_id = r.run_id ORDER BY p.id DESC LIMIT 1000"
    )
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(rows)


# ──────────────────────────────────────────────────────────────────────────────
# SERVE REACT
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    # the frontend is built under /research/ for the ArkaShine site; accept both
    if path == "research" or path.startswith("research/"):
        path = path[len("research"):].lstrip("/")
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


@app.errorhandler(404)
def spa_fallback(err):
    # static_url_path="/" shadows the catch-all above; send unknown non-API
    # paths (React Router pages such as /batch) to the SPA instead of a 404
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=not RESEARCH_MODE,
    )
