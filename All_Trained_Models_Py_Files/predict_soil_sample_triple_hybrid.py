# -*- coding: utf-8 -*-
"""
================================================================================
PREDICTION SCRIPT: TRIPLE-ALGORITHM HYBRID SOIL SPECTRAL MODEL (MODEL 33)
================================================================================
Uses the trained 500-sample production pipelines stored in:
  Final_PKL_Models_TripleHybrid_500/

Combines:
  1. Chemometric PLSR (35%)
  2. SVR-RBF Kernel Regressor (40%)
  3. HistGradientBoosting Regressor (25%)
  4. Tuned SVC Classifier on 81 Chemometric Features
  5. Range & ISO 17025 Compliant Classification

Usage Examples:
  1. Single sample prediction:
     py -3.11 predict_soil_sample_triple_hybrid.py
  2. Predict on an entire Excel file:
     py -3.11 predict_soil_sample_triple_hybrid.py --input new_soil_data.xlsx --output new_predictions.xlsx
================================================================================
"""

import os
import sys
import pickle
import argparse
import numpy as np
import pandas as pd

EXPECTED_BANDS = [
    'nm_410', 'nm_435', 'nm_460', 'nm_485', 'nm_510', 'nm_535', 'nm_560',
    'nm_585', 'nm_610', 'nm_645', 'nm_680', 'nm_705', 'nm_730', 'nm_760',
    'nm_810', 'nm_860', 'nm_900', 'nm_940', 'nm_320', 'nm_280', 'nm_200'
]

NUTRIENTS = [
    ('OC%', 'OC'),
    ('Ca (meq)', 'Ca_meq'),
    ('Mg (meq)', 'Mg_meq'),
    ('N Kg/ha', 'N_Kg_ha'),
    ('P2O5', 'P2O5'),
    ('K2O', 'K2O'),
    ('SO4', 'SO4'),
    ('Fe (ppm)', 'Fe_ppm'),
    ('Mn (ppm)', 'Mn_ppm'),
    ('Cu (ppm)', 'Cu_ppm'),
    ('Zn (ppm)', 'Zn_ppm'),
    ('B (ppm)', 'B_ppm')
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
MODEL_DIR = os.path.join(SCRIPT_DIR, 'Final_PKL_Models_TripleHybrid_500')

def extract_chemometric_features(X_raw):
    """Transforms 21 raw spectral bands into 81 chemometric features."""
    X_raw = np.array(X_raw, dtype=float)
    if X_raw.ndim == 1:
        X_raw = X_raw.reshape(1, -1)
    mean_val = X_raw.mean(axis=1, keepdims=True)
    std_val = X_raw.std(axis=1, keepdims=True) + 1e-8
    X_snv = (X_raw - mean_val) / std_val
    X_d1 = np.diff(X_raw, axis=1)
    X_d2 = np.diff(X_d1, axis=1)
    return np.hstack([X_raw, X_snv, X_d1, X_d2])

def load_models():
    models = {}
    for target_name, file_prefix in NUTRIENTS:
        pkl_path = os.path.join(MODEL_DIR, f"{file_prefix}_TripleHybrid_Model.pkl")
        if not os.path.exists(pkl_path):
            raise FileNotFoundError(f"Missing production model: {pkl_path}")
        with open(pkl_path, 'rb') as f:
            models[target_name] = pickle.load(f)
    return models

def predict_soil_spectra(X_raw, models=None):
    """
    Given an (N, 21) matrix of spectral reflectances, returns a pandas DataFrame
    with Predicted Value and Predicted Class for all 12 soil nutrients.
    """
    if models is None:
        models = load_models()
    
    X_raw = np.array(X_raw, dtype=float)
    if X_raw.ndim == 1:
        X_raw = X_raw.reshape(1, -1)
        
    X_chem = extract_chemometric_features(X_raw)
    n_samples = X_raw.shape[0]
    
    results = {}
    for target_name, bundle in models.items():
        pipe_pls = bundle['pls_regressor']
        pipe_svr = bundle['svr_regressor']
        pipe_hgb = bundle['hgb_regressor']
        w = bundle['weights']
        pipe_clf = bundle['classifier']
        
        # Regression Ensemble
        pred_pls = pipe_pls.predict(X_raw).flatten()
        pred_svr = pipe_svr.predict(X_raw).flatten()
        pred_hgb = pipe_hgb.predict(X_raw).flatten()
        pred_val = (w[0] * pred_pls + w[1] * pred_svr + w[2] * pred_hgb)
        pred_val = np.maximum(0.0, np.round(pred_val, 2))
        
        # Classification
        pred_cls = pipe_clf.predict(X_chem)
        
        results[f"{target_name} Pred Value"] = pred_val
        results[f"{target_name} Pred Class"] = pred_cls
        
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Soil Nutrient Triple-Hybrid Predictor")
    parser.add_argument('--input', type=str, default=None, help="Path to input Excel or CSV file")
    parser.add_argument('--output', type=str, default=None, help="Path to output Excel file")
    args = parser.parse_args()

    models = load_models()
    print("=" * 75)
    print("LOADED 12 TRIPLE-HYBRID PRODUCTION SOIL MODELS (500 SAMPLES)")
    print("Algorithms: Chemometric PLSR (35%) + SVR-RBF (40%) + HistGB (25%) + 81 Feats")
    print("=" * 75)

    if args.input:
        if args.input.endswith('.xlsx') or args.input.endswith('.xls'):
            df_in = pd.read_excel(args.input)
        else:
            df_in = pd.read_csv(args.input)
            
        missing_bands = [b for b in EXPECTED_BANDS if b not in df_in.columns]
        if missing_bands:
            print(f"Error: Missing spectral bands in input file: {missing_bands}")
            sys.exit(1)
            
        X = df_in[EXPECTED_BANDS].values
        df_preds = predict_soil_spectra(X, models)
        out_df = pd.concat([df_in, df_preds], axis=1)
        
        out_path = args.output if args.output else "Soil_Predictions_Output.xlsx"
        out_df.to_excel(out_path, index=False)
        print(f"Predictions saved to: {out_path}")
    else:
        # Run demo on Sample 0 from data.xlsx
        data_path = os.path.join(SCRIPT_DIR, 'data.xlsx')
        if os.path.exists(data_path):
            df_sample = pd.read_excel(data_path).iloc[:3]
            X_demo = df_sample[EXPECTED_BANDS].values
            df_preds = predict_soil_spectra(X_demo, models)
            print("\nDEMO PREDICTION ON FIRST 3 SAMPLES OF data.xlsx:")
            print(df_preds.to_string())

if __name__ == '__main__':
    main()
