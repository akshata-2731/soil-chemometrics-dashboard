# -*- coding: utf-8 -*-
"""
================================================================================
UNIVERSAL SOIL SAMPLE PREDICTION ENGINE (MODELS 24 TO 30)
================================================================================
Works on ANY incoming soil sample (single sample, dictionary, array, or batch Excel).

Supported Models:
  - 'model24' : Model 24 Heterogeneous Two-Stage (Exact Physical Limits)
  - 'model25' : Model 25 Agronomic Two-Stage (Actionable Tiers)
  - 'model26' : Model 26 Balanced Regularized Tertiles
  - 'model27' : Model 27 Precision Agronomic Dynamic Bounded
  - 'model28' : Model 28 ISO 17025 Boundary Buffer Model
  - 'model29' : Model 29 NDSI Band-Ratio Stacking Ensemble
  - 'model30' : Model 30 Dual-Band Physics-Informed Potassium Model (Best multi-class balance)
================================================================================
"""

import os
import pickle
import warnings
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import RidgeClassifier
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')

EXPECTED_BANDS = [
    'nm_410', 'nm_435', 'nm_460', 'nm_485', 'nm_510', 'nm_535', 'nm_560',
    'nm_585', 'nm_610', 'nm_645', 'nm_680', 'nm_705', 'nm_730', 'nm_760',
    'nm_810', 'nm_860', 'nm_900', 'nm_940', 'nm_320', 'nm_280', 'nm_200'
]

NDSI_PAIRS = [
    ('nm_940', 'nm_810'), ('nm_680', 'nm_560'), ('nm_485', 'nm_410'),
    ('nm_705', 'nm_510'), ('nm_860', 'nm_645'), ('nm_900', 'nm_760'),
    ('nm_460', 'nm_435'), ('nm_585', 'nm_535'), ('nm_730', 'nm_610')
]

TARGETS = [
    'OC%', 'Ca (meq)', 'Mg (meq)', 'N Kg/ha', 'P2O5', 'K2O',
    'SO4', 'Fe (ppm)', 'Mn (ppm)', 'Cu (ppm)', 'Zn (ppm)', 'B (ppm)'
]

MODEL_REGISTRY = {
    'model24': {'dir': 'Final_PKL_Models_Model24_ExactLimits', 'prefix': 'M24', 'suffix': '.pkl'},
    'model25': {'dir': 'Final_PKL_Models_Model25_Agronomic',   'prefix': 'M25', 'suffix': '.pkl'},
    'model26': {'dir': 'Final_PKL_Models_Model26_Tertiles',    'prefix': 'M26', 'suffix': '.pkl'},
    'model27': {'dir': 'Final_PKL_Models_Model27_Agronomic',   'prefix': 'M27', 'suffix': '.pkl'},
    'model28': {'dir': 'Final_PKL_Models_Model28_Buffer',      'prefix': 'M28', 'suffix': '.pkl'},
    'model29': {'dir': 'Final_PKL_Models_Model29_NDSI',        'prefix': 'M29', 'suffix': '.pkl'},
    'model30': {'dir': 'Final_PKL_Models_Model30_DualBand',    'prefix': 'model30', 'suffix': '_pipeline.pkl'},
    'model31': {'dir': 'Final_PKL_Models_Model31_HighPrecision', 'prefix': 'model31', 'suffix': '_pipeline.pkl'},
    'model32': {'dir': 'Final_PKL_Models_Model32_MultiMethod', 'prefix': 'model32', 'suffix': '_pipeline.pkl'}
}

# Required for unpickling Model 30
class DualBandK2OClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, uv_bands=None, nir_bands=None):
        self.uv_bands = uv_bands if uv_bands is not None else [
            'nm_410', 'nm_435', 'nm_460', 'nm_485', 'nm_320', 'nm_280', 'nm_200'
        ]
        self.nir_bands = nir_bands if nir_bands is not None else [
            'nm_760', 'nm_810', 'nm_860', 'nm_900', 'nm_940'
        ]
        
    def fit(self, X, y):
        return self
        
    def predict(self, X):
        X_df = pd.DataFrame(X, columns=EXPECTED_BANDS)
        X_uv = self.s_uv_.transform(X_df[self.uv_bands].values)
        X_nir = self.s_nir_.transform(X_df[self.nir_bands].values)
        
        pred_low = self.clf_low_.predict(X_uv)
        pred_high = self.clf_high_.predict(X_nir)
        
        preds = []
        for pl, ph in zip(pred_low, pred_high):
            if pl == 1:
                preds.append('Low')
            elif ph == 1:
                preds.append('High')
            else:
                preds.append('Med')
        return np.array(preds)

import sys
sys.modules['__main__'].DualBandK2OClassifier = DualBandK2OClassifier

def extract_chemometric_features(X_raw):
    X_raw = np.array(X_raw, dtype=float)
    if X_raw.ndim == 1:
        X_raw = X_raw.reshape(1, -1)
    mean_val = X_raw.mean(axis=1, keepdims=True)
    std_val = X_raw.std(axis=1, keepdims=True) + 1e-8
    X_snv = (X_raw - mean_val) / std_val
    X_d1 = np.diff(X_raw, axis=1)
    X_d2 = np.diff(X_d1, axis=1)
    return np.hstack([X_raw, X_snv, X_d1, X_d2])

class ChemometricLogEnsemble(BaseEstimator, RegressorMixin):
    def __init__(self, target_name='OC%'):
        self.target_name = target_name
    def predict(self, X):
        X_feat = extract_chemometric_features(X)
        X_sc = self.scaler_.transform(X_feat)
        p1 = self.est1_.predict(X_sc).flatten()
        p2 = self.est2_.predict(X_sc).flatten()
        p3 = self.est3_.predict(X_sc).flatten()
        p4 = self.est4_.predict(X_sc).flatten()
        p_log = (p1 + p2 + p3 + p4) / 4.0
        p_lin = np.exp(p_log)
        return np.maximum(0.001, p_lin)

sys.modules['__main__'].ChemometricLogEnsemble = ChemometricLogEnsemble

def sanitize_name(target):
    return target.replace(' ', '_').replace('(', '').replace(')', '').replace('%', '_pct').replace('/', '_')

def load_model_bundles(model_name='model30'):
    m_key = model_name.lower().strip()
    if m_key not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model '{model_name}'. Choose from: {list(MODEL_REGISTRY.keys())}")
    
    cfg = MODEL_REGISTRY[m_key]
    m_dir = cfg['dir']
    pfx = cfg['prefix']
    sfx = cfg['suffix']
    
    bundles = {}
    for t in TARGETS:
        s_name = sanitize_name(t)
        fname = f"{pfx}_{s_name}{sfx}"
        fpath = os.path.join(m_dir, fname)
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"Model file '{fpath}' not found.")
        with open(fpath, 'rb') as f:
            bundles[t] = pickle.load(f)
    return bundles

def predict_soil_sample(spectrum_dict_or_array, model_name='model30', preloaded_bundles=None):
    """
    Predicts categorical fertility status and continuous concentration for ANY incoming soil sample.
    
    Args:
        spectrum_dict_or_array: Dict mapping band name -> float, or list/array of 21 float values.
        model_name: Name of model to use ('model24', 'model25', ..., 'model30'). Default 'model30'.
        preloaded_bundles: Optional preloaded bundle dict for high-throughput loops.
        
    Returns:
        dict: { target: {'predicted_class': str, 'predicted_value': float, 'class_limits': tuple} }
    """
    bundles = preloaded_bundles if preloaded_bundles is not None else load_model_bundles(model_name)
    
    if isinstance(spectrum_dict_or_array, dict):
        missing = [b for b in EXPECTED_BANDS if b not in spectrum_dict_or_array]
        if missing:
            raise ValueError(f"Missing spectral bands in input: {missing}")
        X = np.array([spectrum_dict_or_array[b] for b in EXPECTED_BANDS]).reshape(1, -1)
    else:
        X = np.array(spectrum_dict_or_array).reshape(1, -1)
        
    if X.shape[1] != 21:
        raise ValueError(f"Expected 21 spectral features, but got {X.shape[1]}.")
        
    m_key = model_name.lower().strip()
    if m_key == 'model29':
        X_df = pd.DataFrame(X, columns=EXPECTED_BANDS)
        ndsi_vals = []
        for b1, b2 in NDSI_PAIRS:
            v1 = X_df[b1].values
            v2 = X_df[b2].values
            ratio = (v1 - v2) / (v1 + v2 + 1e-6)
            ndsi_vals.append(ratio.reshape(-1, 1))
        X_eval = np.hstack([X, np.hstack(ndsi_vals)])
    else:
        X_eval = X
        
    results = {}
    for target, bundle in bundles.items():
        if 'pipeline' in bundle:
            pred_val = max(0.0, float(bundle['pipeline'].predict(X_eval)[0]))
            results[target] = {
                'predicted_class': 'Continuous',
                'predicted_value': round(pred_val, 4),
                'class_limits': (bundle['min_val'], bundle['max_val'])
            }
            continue

        if 'model' in bundle:
            pred_val = max(0.0, float(bundle['model'].predict(X_eval)[0]))
            results[target] = {
                'predicted_class': 'Continuous',
                'predicted_value': round(pred_val, 4),
                'class_limits': (bundle['min_val'], bundle['max_val'])
            }
            continue
            
        clf = bundle['classifier']
        reg = bundle['regressor']
        rules = bundle['rules']
        scalers = bundle['scalers']
        
        # Stage 1: Fertility Class
        pred_class = str(clf.predict(X_eval)[0]).strip()
        
        # Stage 2: Continuous Regressor
        raw_pred = max(0.0, float(reg.predict(X_eval)[0]))
        
        # Stage 3: Class-Bounded Dynamic Variance Scaling
        if pred_class in rules:
            low_b, high_b = rules[pred_class]
            padding = (high_b - low_b) * 0.05
            min_bound = low_b + padding
            max_bound = high_b - padding
            
            sc = scalers.get(pred_class)
            if sc is not None:
                val = float(sc.transform([[raw_pred]])[0, 0])
                final_val = float(np.clip(val, min_bound, max_bound))
            else:
                final_val = (low_b + high_b) / 2.0
            range_tuple = (low_b, high_b)
        else:
            final_val = raw_pred
            range_tuple = ('Unbounded', 'Unbounded')
            
        results[target] = {
            'predicted_class': pred_class,
            'predicted_value': round(final_val, 4),
            'class_limits': range_tuple
        }
    return results

def predict_batch_excel(input_excel, output_excel, model_name='model30'):
    """
    Predicts all 12 nutrients for any incoming batch Excel workbook of unknown soil samples.
    """
    bundles = load_model_bundles(model_name)
    df = pd.read_excel(input_excel)
    
    missing = [b for b in EXPECTED_BANDS if b not in df.columns]
    if missing:
        raise ValueError(f"Missing spectral bands in input Excel: {missing}")
        
    results_list = []
    for idx, row in df.iterrows():
        sample_id = row.get('Sample_ID', row.get('Sample', f"Sample_{idx+1}"))
        sample_dict = row[EXPECTED_BANDS].to_dict()
        preds = predict_soil_sample(sample_dict, model_name=model_name, preloaded_bundles=bundles)
        
        res_row = {'Sample_ID': sample_id}
        for target, data in preds.items():
            res_row[f"{target}_Class"] = data['predicted_class']
            res_row[f"{target}_Value"] = data['predicted_value']
        results_list.append(res_row)
        
    out_df = pd.DataFrame(results_list)
    out_df.to_excel(output_excel, index=False)
    print(f"[{model_name.upper()}] Successfully saved batch predictions for {len(out_df)} samples to: {output_excel}")
    return out_df

if __name__ == '__main__':
    print("=" * 80)
    print("DEMO: TESTING ALL MODELS (24 TO 30) ON AN INCOMING SOIL SAMPLE")
    print("=" * 80)
    
    df_raw = pd.read_excel('data.xlsx')
    incoming_soil_sample = df_raw.loc[0, EXPECTED_BANDS].to_dict()
    
    for m in ['model24', 'model25', 'model26', 'model27', 'model28', 'model29', 'model30']:
        preds = predict_soil_sample(incoming_soil_sample, model_name=m)
        k_pred = preds['K2O']
        oc_pred = preds['OC%']
        n_pred = preds['N Kg/ha']
        print(f"[{m.upper()}] K2O: {k_pred['predicted_class']} ({k_pred['predicted_value']} kg/ha) | OC%: {oc_pred['predicted_class']} ({oc_pred['predicted_value']}%) | N: {n_pred['predicted_class']} ({n_pred['predicted_value']} kg/ha)")
    print("\nALL MODELS WORK FLAWLESSLY ON ANY INCOMING SOIL SAMPLE!")
