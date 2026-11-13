"""
Training and Prediction Pipeline: ExtraTrees (LOOCV Validated)
================================================================
Generated for Soil Spectroscopy Data.
Run this script to retrain all 12 models with Leave-One-Out Cross-Validation (LOOCV).
"""

import os
import pandas as pd
import numpy as np
import joblib
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.kernel_ridge import KernelRidge
from sklearn.svm import SVR
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

class SpectralRatioTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, band1_idx=10, band2_idx=0):
        self.band1_idx = band1_idx
        self.band2_idx = band2_idx
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        X = np.asarray(X)
        b1, b2 = X[:, self.band1_idx], X[:, self.band2_idx]
        return np.column_stack([b1 / (b2 + 1e-6), (b1 - b2) / (b1 + b2 + 1e-6)])

def train():
    data_file = "../data.xlsx" if os.path.exists("../data.xlsx") else "data.xlsx"
    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    soil_cols = [c for c in df.columns if not c.startswith('nm_')]
    
    os.makedirs("models", exist_ok=True)
    loo = LeaveOneOut()
    
    print(f"Executing Leave-One-Out Cross-Validation (LOOCV) for ExtraTrees...")
    for target in soil_cols:
        sub = df.dropna(subset=[target])
        X = sub[spec_cols].values
        y = sub[target].values
        
        model_name = "ExtraTrees"
        if model_name == 'ExtraTrees':
            pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA(n_components=2)), ('reg', ExtraTreesRegressor(n_estimators=100, random_state=42))])
        elif model_name == 'RandomForest':
            pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA(n_components=2)), ('reg', RandomForestRegressor(n_estimators=100, random_state=42))])
        elif model_name == 'KernelRidge':
            pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA(n_components=2)), ('reg', KernelRidge(kernel='rbf', alpha=0.1, gamma=0.2))])
        elif model_name == 'SpectralRatio':
            pipe = Pipeline([('ratio', SpectralRatioTransformer(10, 0)), ('scaler', StandardScaler()), ('reg', SVR(kernel='rbf', C=30, gamma='scale', epsilon=0.05))])
            
        y_pred = np.maximum(0, cross_val_predict(pipe, X, y, cv=loo))
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        acc = (1.0 - (rmse / (y.max() - y.min()))) * 100.0
        
        # Save production model
        pipe.fit(X, y)
        clean_name = target.replace('/', '_').replace(' ', '_').replace('%', 'Pct').replace('(', '').replace(')', '')
        model_path = os.path.join("models", f"{clean_name}_ExtraTrees.joblib")
        joblib.dump(pipe, model_path)
        print(f"{target:<12}: LOOCV Accuracy = {acc:.2f}% | R2 = {r2*100:.2f}% -> Model saved: {model_path}")

def predict_new(spectrum_21_bands):
    spectrum = np.array(spectrum_21_bands).reshape(1, -1)
    preds = {}
    for f in sorted(os.listdir("models")):
        if f.endswith('.joblib'):
            target = f.replace("_ExtraTrees.joblib", "")
            m = joblib.load(os.path.join("models", f))
            preds[target] = round(max(0.0, float(m.predict(spectrum)[0])), 4)
    return preds

if __name__ == '__main__':
    train()
