# -*- coding: utf-8 -*-
"""
Inference Script: Predict All 12 Soil Nutrients for New Samples
==============================================================
Uses the trained production models from 'models_75pct_loocv/' (all >= 75% LOOCV Accuracy)
"""

import os
import joblib
import pandas as pd
import numpy as np

MODELS_DIR = 'models_75pct_loocv'

# Model files mapping
TARGET_MODELS = {
    'OC%': 'OCPct_best_75pct.joblib',
    'Ca (meq)': 'Ca_meq_best_75pct.joblib',
    'Mg (meq)': 'Mg_meq_best_75pct.joblib',
    'N Kg/ha': 'N_Kg_ha_best_75pct.joblib',
    'P2O5': 'P2O5_best_75pct.joblib',
    'K2O': 'K2O_best_75pct.joblib',
    'SO4': 'SO4_best_75pct.joblib',
    'Fe (ppm)': 'Fe_ppm_best_75pct.joblib',
    'Mn (ppm)': 'Mn_ppm_best_75pct.joblib',
    'Cu (ppm)': 'Cu_ppm_best_75pct.joblib',
    'Zn (ppm)': 'Zn_ppm_best_75pct.joblib',
    'B (ppm)': 'B_ppm_best_75pct.joblib'
}

EXPECTED_BANDS = [
    'nm_410', 'nm_435', 'nm_460', 'nm_485', 'nm_510', 'nm_535', 'nm_560',
    'nm_585', 'nm_610', 'nm_645', 'nm_680', 'nm_705', 'nm_730', 'nm_760',
    'nm_810', 'nm_860', 'nm_900', 'nm_940', 'nm_320', 'nm_280', 'nm_200'
]

def load_all_models(models_dir=MODELS_DIR):
    """Loads all 12 trained nutrient models into memory."""
    loaded_models = {}
    for target, filename in TARGET_MODELS.items():
        filepath = os.path.join(models_dir, filename)
        if os.path.exists(filepath):
            loaded_models[target] = joblib.load(filepath)
        else:
            raise FileNotFoundError(f"Model file '{filepath}' not found. Please train models first.")
    return loaded_models

def predict_single_sample(spectrum_dict_or_array, models=None):
    """
    Predicts 12 soil nutrients for a single spectral sample.
    
    Args:
        spectrum_dict_or_array: Dict with band names (e.g. {'nm_410': 1700, ...}) 
                                or a 1D array/list of 21 reflectance values.
        models: Optional pre-loaded models dict (avoids reloading from disk on each call).
        
    Returns:
        dict of {nutrient_name: predicted_value}
    """
    if models is None:
        models = load_all_models()
        
    if isinstance(spectrum_dict_or_array, dict):
        X = np.array([spectrum_dict_or_array[b] for b in EXPECTED_BANDS]).reshape(1, -1)
    else:
        X = np.array(spectrum_dict_or_array).reshape(1, -1)
        
    if X.shape[1] != 21:
        raise ValueError(f"Expected 21 spectral features, but got {X.shape[1]}.")
        
    predictions = {}
    for target, pipe in models.items():
        pred = pipe.predict(X)
        if hasattr(pred, 'ndim') and pred.ndim > 1:
            pred = pred.flatten()
        val = max(0.0, float(pred[0]))
        predictions[target] = round(val, 4)
        
    return predictions

def predict_from_excel(input_excel_file, output_excel_file=None):
    """
    Predicts 12 soil nutrients for a batch of samples in an Excel file.
    """
    models = load_all_models()
    df = pd.read_excel(input_excel_file)
    
    missing_bands = [b for b in EXPECTED_BANDS if b not in df.columns]
    if missing_bands:
        raise ValueError(f"Missing spectral bands in input file: {missing_bands}")
        
    X = df[EXPECTED_BANDS].values
    results_df = df.copy()
    
    for target, pipe in models.items():
        preds = pipe.predict(X)
        if hasattr(preds, 'ndim') and preds.ndim > 1:
            preds = preds.flatten()
        preds = np.maximum(0.0, preds)
        results_df[f"{target}_Predicted"] = np.round(preds, 4)
        
    if output_excel_file:
        results_df.to_excel(output_excel_file, index=False)
        print(f"Predictions saved to: '{output_excel_file}'")
        
    return results_df

if __name__ == '__main__':
    print("=" * 70)
    print("DEMO: TESTING PREDICTION ON SAMPLE 1 FROM DATASET")
    print("=" * 70)
    
    raw = pd.read_excel('data.xlsx')
    sample_1_spectra = raw.loc[0, EXPECTED_BANDS].to_dict()
    
    print("\nLoading models and predicting 12 soil nutrients...")
    preds = predict_single_sample(sample_1_spectra)
    
    print("\nPredicted Nutrients for Sample 1:")
    print("-" * 45)
    for nutrient, val in preds.items():
        actual = raw.loc[0, nutrient] if nutrient in raw.columns else 'N/A'
        print(f"{nutrient:<12}: Pred = {val:10.4f} | Actual = {actual}")
    print("-" * 45)
