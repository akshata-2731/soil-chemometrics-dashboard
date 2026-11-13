import base64, os

APP_CODE = """
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

LOGICS_DEF_DIR   = PROJECT_ROOT / "logics" / "definitions"
LOGICS_IMPL_DIR  = PROJECT_ROOT / "logics" / "implementations"
CALIBRATION_DIR  = PROJECT_ROOT / "calibration"
CALIBRATION_FILE = CALIBRATION_DIR / "calibration.json"
MODELS_DIR       = PROJECT_ROOT / "models"
DB_PATH          = PROJECT_ROOT / "history.db"

for d in [LOGICS_DEF_DIR, LOGICS_IMPL_DIR, CALIBRATION_DIR, MODELS_DIR]:
    os.makedirs(d, exist_ok=True)

WAVELENGTH_ORDER = [410,435,460,485,510,535,560,585,610,645,680,705,730,760,810,860,900,940,320,280,200]
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
            impl_path = os.path.join(LOGICS_IMPL_DIR, d.get("id","") + ".py")
            d["status"] = "Implemented" if os.path.exists(impl_path) else "NOT IMPLEMENTED"
            logics.append(d)
        except Exception:
            pass
    logics.sort(key=lambda x: x.get("id",""))
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


@app.route("/api/models", methods=["GET"])
def get_models():
    models = []
    for f in glob.glob(os.path.join(MODELS_DIR, "*.pkl")):
        basename = os.path.basename(f)
        models.append({"id": basename, "name": basename, "type": "ML Model"})
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


def execute_prediction(sample_data, target, method_type, method_id, is_cal_required):
    wvs    = extract_wavelengths(sample_data)
    actual = extract_actual(sample_data, target)

    # ── ML path ──────────────────────────────────────────────────────────────
    if method_type == "ml":
        m_path = os.path.join(MODELS_DIR, method_id)
        if not os.path.exists(m_path):
            raise Exception("ML Model file not found: " + method_id)

        model_payload = joblib.load(m_path)
        features_used = FEATURE_NAMES

        if isinstance(model_payload, dict) and "model" in model_payload:
            m_obj = model_payload["model"]
            if not ("scaler" in m_obj and "classifier" in m_obj and "regressors" in m_obj):
                raise Exception("Model structure incompatible: missing scaler/classifier/regressors")
            scaler     = m_obj["scaler"]
            classifier = m_obj["classifier"]
            regressors = m_obj["regressors"]
            features   = model_payload.get("features", FEATURE_NAMES)
            features_used = list(features)
            input_df   = pd.DataFrame([wvs], columns=FEATURE_NAMES)[features_used]
            X_scaled   = scaler.transform(input_df)
            pred_class = classifier.predict(X_scaled)[0]
            reg        = regressors.get(pred_class)
            if reg is None:
                raise Exception("No regressor found for class: " + str(pred_class))
            raw_pred   = float(reg.predict(X_scaled)[0])
            if target in THRESHOLDS:
                lo   = THRESHOLDS[target].get("Low", 0.0)
                hi   = THRESHOLDS[target].get("Medium", 0.0)
                pred = float(soft_clamp(raw_pred, lo, hi, pred_class, target))
            else:
                pred = raw_pred
        else:
            features = getattr(model_payload, "feature_names_in_", None)
            if features is None or isinstance(features, int):
                features = FEATURE_NAMES
            features_used = list(features)
            input_df = pd.DataFrame([wvs], columns=FEATURE_NAMES)
            if set(features_used).issubset(set(FEATURE_NAMES)):
                pred = float(model_payload.predict(input_df[features_used])[0])
            else:
                pred = float(model_payload.predict(input_df)[0])
            raw_pred = pred

        min_limit, max_limit, is_clamped, _ = get_documented_limits("ml", method_id)
        final_pred = clamp(pred, min_limit, max_limit) if (is_clamped and min_limit is not None and max_limit is not None) else pred

        return {
            "nutrient": target, "selected_method": method_id, "executed_method": method_id,
            "method_type": "ML Model", "calibration_required": False,
            "calibration_source": "Not Required (ML)", "wavelengths_used": features_used,
            "raw_prediction": raw_pred, "clamp_applied": bool(is_clamped),
            "clamp_rule": "[" + str(min_limit) + ", " + str(max_limit) + "]" if is_clamped else "None",
            "final_prediction": final_pred, "actual": actual,
            "error": round(final_pred - actual, 4) if actual is not None else None,
            "status": get_nutrient_status(target, final_pred)
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

        if logic_def.get("calibration_required", False) and not is_cal_required:
            raise Exception("Selected Logic requires calibration. Please select Calibration = Required.")

        cal_data   = None
        cal_source = "Not Required"

        if is_cal_required:
            if not os.path.exists(CALIBRATION_FILE):
                raise Exception("Calibration Required but calibration.json is missing. Please upload it.")
            with open(CALIBRATION_FILE, "r", encoding="utf-8") as cf:
                all_cals = json.load(cf)
            if target not in all_cals:
                raise Exception("Calibration data missing for " + target + " in calibration.json")
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
        raw_pred = float(mod.predict(wvs, cal_data))

        min_limit, max_limit, is_clamped, _ = get_documented_limits("logic", method_id)
        final_pred = clamp(raw_pred, min_limit, max_limit) if (is_clamped and min_limit is not None and max_limit is not None) else raw_pred
        features_used = logic_def.get("features", FEATURE_NAMES)

        return {
            "nutrient": target, "selected_method": method_id, "executed_method": method_id,
            "method_type": "Logic", "calibration_required": bool(is_cal_required),
            "calibration_source": cal_source, "wavelengths_used": features_used,
            "raw_prediction": raw_pred, "clamp_applied": bool(is_clamped),
            "clamp_rule": "[" + str(min_limit) + ", " + str(max_limit) + "]" if is_clamped else "None",
            "final_prediction": final_pred, "actual": actual,
            "error": round(final_pred - actual, 4) if actual is not None else None,
            "status": get_nutrient_status(target, final_pred)
        }
    else:
        raise Exception("Unknown method type: " + str(method_type))


def process_request(mode, data):
    run_id  = "RUN-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6].upper()
    samples = data.get("samples", [])
    targets = data.get("targets", [])
    mapping = data.get("mapping", {})
    results = []

    for s in samples:
        s_id = s.get("Sample_ID", "Unknown")
        for t in targets:
            conf = mapping.get(t)
            if not conf:
                continue
            try:
                res = execute_prediction(
                    sample_data    = s,
                    target         = t,
                    method_type    = conf.get("method_type"),
                    method_id      = conf.get("method_id"),
                    is_cal_required= conf.get("calibration_required", False)
                )
            except Exception as e:
                res = {
                    "nutrient": t, "selected_method": conf.get("method_id","Unknown"),
                    "executed_method": "ERROR", "method_type": conf.get("method_type","Unknown"),
                    "calibration_required": conf.get("calibration_required", False),
                    "calibration_source": "ERROR", "wavelengths_used": [],
                    "raw_prediction": None, "clamp_applied": False, "clamp_rule": "N/A",
                    "final_prediction": None, "actual": None, "error": None,
                    "status": "FAILED: " + str(e)
                }
            res["sample_id"] = s_id
            results.append(res)

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
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
""".lstrip()

with open(r"c:\Users\hp\Downloads\soil cali\app.py", "w", encoding="utf-8") as f:
    f.write(APP_CODE)

print("Written:", len(APP_CODE.splitlines()), "lines")
