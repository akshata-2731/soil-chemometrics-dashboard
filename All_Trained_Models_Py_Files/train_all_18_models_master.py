# -*- coding: utf-8 -*-
"""
MASTER TRAINING & LOOCV EVALUATION SCRIPT: ALL 18 SOIL SPECTROSCOPY MODELS
==========================================================================
This script trains, cross-validates, and saves all 18 machine learning and
chemometric models for the 12 soil nutrient parameters using strict Leave-One-Out
Cross-Validation (LOOCV).

Key Features:
- Complete standalone pipeline for all 18 models.
- 0% Data Leakage: strictly out-of-fold cross_val_predict(..., cv=LeaveOneOut()).
- Computes Ratio Accuracy: min(Actual, Pred) / max(Actual, Pred) * 100%.
- Generates 18 individual clean uncolored Excel workbooks (Sheet 1 = Summary, Sheets 2-13 = 12 Nutrients).
- Saves all trained production models as .joblib binaries into 'saved_models_18/'.

Usage:
  py train_all_18_models_master.py                 # Train all 18 models
  py train_all_18_models_master.py --model 1       # Train only Model 1
  py train_all_18_models_master.py --list          # List all 18 model architectures
"""

import os
import sys
import argparse
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import joblib
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Scikit-learn & Scipy components
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA, KernelPCA
from sklearn.manifold import Isomap
from sklearn.cross_decomposition import PLSRegression
from sklearn.svm import SVR
from sklearn.ensemble import (
    ExtraTreesRegressor,
    RandomForestRegressor,
    GradientBoostingRegressor,
    AdaBoostRegressor,
    VotingRegressor
)
from sklearn.kernel_ridge import KernelRidge
from sklearn.linear_model import BayesianRidge, ElasticNet, HuberRegressor, RidgeCV
from sklearn.neighbors import KNeighborsRegressor
from lightgbm import LGBMRegressor
from sklearn.base import BaseEstimator, TransformerMixin, RegressorMixin
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from scipy.interpolate import RBFInterpolator

# ---------------------------------------------------------------------------
# CUSTOM TRANSFORMERS & GEOMETRIC INTERPOLATORS
# ---------------------------------------------------------------------------

class SpectralRatioTransformer(BaseEstimator, TransformerMixin):
    """2D Fixed Spectral Ratio: 680nm/410nm ratio and normalized difference index."""
    def __init__(self, b1=10, b2=0):
        self.b1 = b1
        self.b2 = b2
    def fit(self, X, y=None): return self
    def transform(self, X):
        X = np.asarray(X)
        r = X[:, self.b1] / (X[:, self.b2] + 1e-6)
        n = (X[:, self.b1] - X[:, self.b2]) / (X[:, self.b1] + X[:, self.b2] + 1e-6)
        return np.column_stack([r, n])


class Optimal2DBandPairTransformer(BaseEstimator, TransformerMixin):
    """2D Optimal Band Pair: finds the most correlated dual-band pair for each nutrient."""
    def __init__(self, top_pair=(10, 0)):
        self.top_pair = top_pair
    def fit(self, X, y=None):
        if y is None: return self
        X = np.asarray(X)
        y = np.asarray(y)
        n_feats = X.shape[1]
        best_corr = -1
        best_p = (0, 1)
        for i in range(n_feats):
            for j in range(i + 1, n_feats):
                ratio = X[:, i] / (X[:, j] + 1e-6)
                c = abs(np.corrcoef(ratio, y)[0, 1])
                if not np.isnan(c) and c > best_corr:
                    best_corr = c
                    best_p = (i, j)
        self.top_pair = best_p
        return self
    def transform(self, X):
        X = np.asarray(X)
        i, j = self.top_pair
        r = X[:, i] / (X[:, j] + 1e-6)
        ndi = (X[:, i] - X[:, j]) / (X[:, i] + X[:, j] + 1e-6)
        return np.column_stack([r, ndi])


class ThinPlateSpline3DRegressor(BaseEstimator, RegressorMixin):
    """3D Thin-Plate Spline: fits a biharmonic minimum-bending-energy 3D surface."""
    def __init__(self, smoothing=1.5, kernel='thin_plate_spline'):
        self.smoothing = smoothing
        self.kernel = kernel
    def fit(self, X, y):
        self.X_ = np.asarray(X)
        self.y_ = np.asarray(y)
        self.rbf_ = RBFInterpolator(self.X_, self.y_, smoothing=self.smoothing, kernel=self.kernel)
        return self
    def predict(self, X):
        X = np.asarray(X)
        return self.rbf_(X)


# ---------------------------------------------------------------------------
# ALL 18 MODEL ARCHITECTURE BUILDERS
# ---------------------------------------------------------------------------

ALL_18_MODELS = {
    1: {
        'id': 'Model_01',
        'name': 'Chemometric Partial Least Squares Regression (PLSR)',
        'file': 'Model_01_Chemometric_PLSR_LOOCV_Results.xlsx',
        'desc': 'Decomposes simultaneous X <-> y covariance into orthogonal latent components.',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('pls', PLSRegression(n_components=4 if tgt in ['Fe (ppm)', 'Zn (ppm)'] else 3))
        ])
    },
    2: {
        'id': 'Model_02',
        'name': 'Full-Spectrum 21D SVR-RBF',
        'file': 'Model_02_Full_21D_SVR_RBF_LOOCV_Results.xlsx',
        'desc': 'Non-linear RKHS projection over all 21 spectral wavelengths without 2D dimensionality loss.',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('svr', SVR(kernel='rbf', C=50, gamma='scale', epsilon=0.05))
        ])
    },
    3: {
        'id': 'Model_03',
        'name': '3D Extra-Trees Regressor',
        'file': 'Model_03_3D_ExtraTrees_LOOCV_Results.xlsx',
        'desc': '100 randomized orthogonal decision tree splits on (PC1, PC2) spectral plane.',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('pca', PCA(n_components=2)),
            ('reg', ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42))
        ])
    },
    4: {
        'id': 'Model_04',
        'name': '3D Random Forest Regressor',
        'file': 'Model_04_3D_RandomForest_LOOCV_Results.xlsx',
        'desc': '100 bootstrapped decision tree surfaces on (PC1, PC2) spectral coordinates.',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('pca', PCA(n_components=2)),
            ('reg', RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42))
        ])
    },
    5: {
        'id': 'Model_05',
        'name': '3D Kernel Ridge Regression (KRR-RBF)',
        'file': 'Model_05_3D_KernelRidge_LOOCV_Results.xlsx',
        'desc': 'Dual-space non-linear RBF regularized smooth continuous surface on (PC1, PC2).',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('pca', PCA(n_components=2)),
            ('reg', KernelRidge(alpha=0.5, kernel='rbf', gamma=0.1))
        ])
    },
    6: {
        'id': 'Model_06',
        'name': '2D Spectral Ratio Index Regressor',
        'file': 'Model_06_2D_SpectralRatio_LOOCV_Results.xlsx',
        'desc': 'Bivariate optical absorption contrast (680nm/410nm) + NDI via SVR-RBF.',
        'builder': lambda tgt: Pipeline([
            ('ratio', SpectralRatioTransformer(10, 0)),
            ('scaler', StandardScaler()),
            ('reg', SVR(kernel='rbf', C=30, gamma='scale', epsilon=0.05))
        ])
    },
    7: {
        'id': 'Model_07',
        'name': '3D Support Vector Regression (SVR-RBF on PC1, PC2)',
        'file': 'Model_07_3D_SVR_RBF_LOOCV_Results.xlsx',
        'desc': 'Maximum-margin support vector boundary with epsilon-insensitive noise tube on (PC1, PC2).',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('pca', PCA(n_components=2)),
            ('svr', SVR(kernel='rbf', C=30, gamma='scale', epsilon=0.05))
        ])
    },
    8: {
        'id': 'Model_08',
        'name': 'Gradient Boosting Regressor (GBR)',
        'file': 'Model_08_Gradient_Boosting_LOOCV_Results.xlsx',
        'desc': 'Iteratively fits 60 decision trees to minimize negative loss gradients.',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('pca', PCA(n_components=3)),
            ('gbr', GradientBoostingRegressor(n_estimators=60, max_depth=3, learning_rate=0.05, random_state=42))
        ])
    },
    9: {
        'id': 'Model_09',
        'name': 'Bayesian Ridge Regression',
        'file': 'Model_09_Bayesian_Ridge_LOOCV_Results.xlsx',
        'desc': 'Linear regression with spherical Gaussian priors, automatically learning L2 regularization.',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('pca', PCA(n_components=3)),
            ('br', BayesianRidge(max_iter=300))
        ])
    },
    10: {
        'id': 'Model_10',
        'name': 'KNN Distance-Weighted Regressor',
        'file': 'Model_10_KNN_Distance_Reg_LOOCV_Results.xlsx',
        'desc': 'Non-parametric instance regression computing inverse-distance weighted spectral neighbors.',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('pca', PCA(n_components=3)),
            ('knn', KNeighborsRegressor(n_neighbors=5, weights='distance', metric='manhattan'))
        ])
    },
    11: {
        'id': 'Model_11',
        'name': 'ElasticNet Chemometric Regressor',
        'file': 'Model_11_ElasticNet_LOOCV_Results.xlsx',
        'desc': 'Regularized linear regression combining L1 (sparsity) and L2 (shrinkage) grouping penalties.',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('enet', ElasticNet(alpha=0.08, l1_ratio=0.4, max_iter=2000, random_state=42))
        ])
    },
    12: {
        'id': 'Model_12',
        'name': 'LightGBM Boosted Decision Trees',
        'file': 'Model_12_LightGBM_Trees_LOOCV_Results.xlsx',
        'desc': 'Histogram-based leaf-wise splitting for fast, non-linear spectral nutrient mapping.',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('pca', PCA(n_components=3)),
            ('lgbm', LGBMRegressor(n_estimators=60, max_depth=3, learning_rate=0.05, random_state=42, verbosity=-1))
        ])
    },
    13: {
        'id': 'Model_13',
        'name': 'AdaBoost Regressor (Adaptive Boosting)',
        'file': 'Model_13_AdaBoost_Regressor_LOOCV_Results.xlsx',
        'desc': 'Adaptively concentrates successive weak tree regressors on hard-to-predict spectral samples.',
        'builder': lambda tgt: Pipeline([
            ('scaler', StandardScaler()),
            ('pca', PCA(n_components=3)),
            ('ada', AdaBoostRegressor(n_estimators=50, learning_rate=0.05, loss='exponential', random_state=42))
        ])
    },
    14: {
        'id': 'Model_14',
        'name': 'Weighted Synergy Voting Ensemble (SVR + AdaBoost + PLSR)',
        'file': 'Model_14_Weighted_Voting_Ensemble_LOOCV_Results.xlsx',
        'desc': 'Weighted ensemble of SVR-RBF, AdaBoost, and PLSR canceling out uncorrelated prediction errors.',
        'builder': lambda tgt: VotingRegressor(
            estimators=[
                ('svr', Pipeline([('sc', StandardScaler()), ('reg', SVR(C=50, gamma='scale', epsilon=0.05))])),
                ('ada', Pipeline([('sc', StandardScaler()), ('pca', PCA(n_components=3)), ('reg', AdaBoostRegressor(n_estimators=30, learning_rate=0.05, random_state=42))])),
                ('pls', Pipeline([('sc', StandardScaler()), ('reg', PLSRegression(n_components=3))]))
            ],
            weights=[2.0, 1.5, 1.0]
        )
    },
    15: {
        'id': 'Model_15',
        'name': 'Huber Robust Regressor (Outlier Resilient)',
        'file': 'Model_15_Huber_Robust_LOOCV_Results.xlsx',
        'desc': 'Quadratic-linear hybrid loss function preventing distortion from extreme natural soil outliers.',
        'builder': lambda tgt: Pipeline([
            ('sc', RobustScaler()),
            ('pca', PCA(n_components=3)),
            ('reg', HuberRegressor(epsilon=1.35, max_iter=500))
        ])
    },
    16: {
        'id': 'Model_16',
        'name': '3D Isomap Geodesic Manifold + SVR',
        'file': 'Model_16_3D_Isomap_Manifold_LOOCV_Results.xlsx',
        'desc': 'Unrolls non-linear spectral manifold curvature using graph geodesic shortest path distances.',
        'builder': lambda tgt: Pipeline([
            ('sc', StandardScaler()),
            ('iso', Isomap(n_components=3, n_neighbors=8)),
            ('reg', SVR(kernel='rbf', C=30, gamma='scale', epsilon=0.05))
        ])
    },
    17: {
        'id': 'Model_17',
        'name': '2D Optimal Band-Pair Absorption Index + SVR',
        'file': 'Model_17_2D_Optimal_BandPair_LOOCV_Results.xlsx',
        'desc': 'Searches all 210 spectral wavelength pairs to isolate the specific dual-band overtone per nutrient.',
        'builder': lambda tgt: Pipeline([
            ('obp', Optimal2DBandPairTransformer()),
            ('sc', StandardScaler()),
            ('reg', SVR(kernel='rbf', C=30, gamma='scale', epsilon=0.05))
        ])
    },
    18: {
        'id': 'Model_18',
        'name': '3D Thin-Plate Spline (TPS) Surface Interpolator',
        'file': 'Model_18_3D_Thin_Plate_Spline_LOOCV_Results.xlsx',
        'desc': 'Biharmonic minimum-bending-energy 3D surface over (PC1, PC2) with zero edge-boundary tearing.',
        'builder': lambda tgt: Pipeline([
            ('sc', StandardScaler()),
            ('pca', PCA(n_components=2)),
            ('tps', ThinPlateSpline3DRegressor(smoothing=1.5, kernel='thin_plate_spline'))
        ])
    }
}

# 12 Target Nutrients
TARGET_NUTRIENTS = [
    ('OCPct', 'OC%', 'Organic Carbon (%)'),
    ('Ca_meq', 'Ca (meq)', 'Available Calcium (meq/100g)'),
    ('Mg_meq', 'Mg (meq)', 'Available Magnesium (meq/100g)'),
    ('N_Kg_ha', 'N Kg_ha', 'Available Nitrogen (Kg/ha)'),
    ('P2O5', 'P2O5', 'Available Phosphorus (Kg/ha)'),
    ('K2O', 'K2O', 'Available Potassium (Kg/ha)'),
    ('SO4', 'SO4', 'Available Sulfate (ppm)'),
    ('Fe_ppm', 'Fe (ppm)', 'Available Iron (ppm)'),
    ('Mn_ppm', 'Mn (ppm)', 'Available Manganese (ppm)'),
    ('Cu_ppm', 'Cu (ppm)', 'Available Copper (ppm)'),
    ('Zn_ppm', 'Zn (ppm)', 'Available Zinc (ppm)'),
    ('B_ppm', 'B (ppm)', 'Available Boron (ppm)')
]

# Formatting styles (Clean normal uncolored Excel)
NO_FILL = PatternFill(fill_type=None)
FONT_TITLE = Font(name='Calibri', size=12, bold=True, color='000000')
FONT_SUBTITLE = Font(name='Calibri', size=11, bold=True, color='333333')
FONT_HEADER = Font(name='Calibri', size=11, bold=True, color='000000')
FONT_DATA = Font(name='Calibri', size=11, bold=False, color='000000')
FONT_BOLD = Font(name='Calibri', size=11, bold=True, color='000000')
FONT_NOTE = Font(name='Calibri', size=10, italic=True, color='555555')
BORDER_THIN = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)


def train_and_evaluate_model(model_num, df, spec_cols, soil_cols, save_models=True, models_dir='saved_models_18'):
    """Trains and cross-validates a single model architecture across all 12 nutrients."""
    m_info = ALL_18_MODELS[model_num]
    m_name = m_info['name']
    out_file = m_info['file']
    desc = m_info['desc']
    builder_fn = m_info['builder']
    n_samples = len(df)
    
    print(f"\n[{model_num:02d}/18] Training: {m_name}")
    print(f"       Description: {desc}")
    print(f"       Export File: {out_file}")
    
    loo = LeaveOneOut()
    nutrient_results = []
    
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    
    # SHEET 1: LOOCV_Summary
    ws_sum = wb.create_sheet(title='LOOCV_Summary')
    ws_sum.views.sheetView[0].showGridLines = True
    
    ws_sum.merge_cells(start_row=1, start_column=1, end_row=1, end_column=7)
    t1 = ws_sum.cell(row=1, column=1, value=f"LOOCV BENCHMARK SUMMARY: {m_name.upper()}")
    t1.font = FONT_TITLE
    t1.fill = NO_FILL
    t1.alignment = Alignment(horizontal='center', vertical='center')
    ws_sum.row_dimensions[1].height = 28
    
    ws_sum.merge_cells(start_row=2, start_column=1, end_row=2, end_column=7)
    t2 = ws_sum.cell(row=2, column=1, value=f"Architecture: {m_name} | Cross-Validation: Leave-One-Out (LOOCV) | Samples: {n_samples}")
    t2.font = FONT_SUBTITLE
    t2.fill = NO_FILL
    t2.alignment = Alignment(horizontal='center', vertical='center')
    ws_sum.row_dimensions[2].height = 22
    
    sum_headers = ['Target Nutrient', 'Full Nutrient Name', 'Valid Samples', 'LOOCV Ratio Accuracy (%)', 'LOOCV RMSE', 'LOOCV MAE', 'Sample Accuracy Range']
    for c_idx, h in enumerate(sum_headers, 1):
        c = ws_sum.cell(row=3, column=c_idx, value=h)
        c.font = FONT_HEADER
        c.fill = NO_FILL
        c.border = BORDER_THIN
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws_sum.row_dimensions[3].height = 28
    
    for r_idx, (col_prefix, sheet_tab, full_name) in enumerate(TARGET_NUTRIENTS, 4):
        tgt_col = [c for c in soil_cols if col_prefix.split('_')[0] in c or sheet_tab in c][0]
        sub = df.dropna(subset=[tgt_col])
        v_idx = sub.index
        X = sub[spec_cols].values
        y = sub[tgt_col].values
        n_v = len(y)
        
        # 1. Strict LOOCV Cross-Validation
        pipe = builder_fn(tgt_col)
        y_pred = cross_val_predict(pipe, X, y, cv=loo)
        if hasattr(y_pred, 'ndim') and y_pred.ndim > 1:
            y_pred = y_pred.flatten()
        y_pred = np.maximum(0.0, y_pred)
        
        # 2. Residual errors & ratio accuracy
        diff = np.abs(y - y_pred)
        mae = float(np.mean(diff))
        rmse = float(np.sqrt(np.mean((y - y_pred)**2)))
        
        sample_accs = [
            round((min(a, p) / max(a, p)) * 100.0 if max(a, p) > 0 else (100.0 if a == 0 and p == 0 else 0.0), 2)
            for a, p in zip(y, y_pred)
        ]
        avg_acc = float(np.mean(sample_accs))
        min_acc = float(np.min(sample_accs))
        max_acc = float(np.max(sample_accs))
        
        # 3. Fit production model on all valid samples & save binary
        if save_models:
            os.makedirs(models_dir, exist_ok=True)
            pipe_final = builder_fn(tgt_col)
            pipe_final.fit(X, y)
            model_save_path = os.path.join(models_dir, f"{m_info['id']}_{col_prefix}.joblib")
            joblib.dump(pipe_final, model_save_path)
            
        act_arr = np.full(n_samples, np.nan)
        pred_arr = np.full(n_samples, np.nan)
        err_arr = np.full(n_samples, np.nan)
        acc_arr = np.full(n_samples, np.nan)
        
        act_arr[v_idx] = np.round(y, 4)
        pred_arr[v_idx] = np.round(y_pred, 4)
        err_arr[v_idx] = np.round(diff, 4)
        acc_arr[v_idx] = sample_accs
        
        nutrient_results.append({
            'sheet_tab': sheet_tab,
            'full_name': full_name,
            'act': act_arr,
            'pred': pred_arr,
            'err': err_arr,
            'acc': acc_arr,
            'rmse': rmse,
            'mae': mae,
            'avg_acc': avg_acc,
            'min_acc': min_acc,
            'max_acc': max_acc,
            'n_v': n_v
        })
        
        row_vals = [
            sheet_tab,
            full_name,
            n_v,
            round(avg_acc, 2),
            round(rmse, 4),
            round(mae, 4),
            f"{min_acc:.1f}% - {max_acc:.1f}%"
        ]
        for c_idx, val in enumerate(row_vals, 1):
            c = ws_sum.cell(row=r_idx, column=c_idx, value=val)
            c.font = FONT_DATA
            c.fill = NO_FILL
            c.border = BORDER_THIN
            if c_idx in [1, 3, 7]: c.alignment = Alignment(horizontal='center', vertical='center')
            elif c_idx == 2: c.alignment = Alignment(horizontal='left', vertical='center')
            else: c.alignment = Alignment(horizontal='right', vertical='center')
        ws_sum.row_dimensions[r_idx].height = 22
        
    # Average Summary Row
    avg_row_idx = len(TARGET_NUTRIENTS) + 4
    ws_sum.cell(row=avg_row_idx, column=1, value='AVERAGE')
    ws_sum.cell(row=avg_row_idx, column=2, value='Mean Across All 12 Soil Nutrients')
    ws_sum.cell(row=avg_row_idx, column=3, value=n_samples)
    ws_sum.cell(row=avg_row_idx, column=4, value=round(float(np.mean([n['avg_acc'] for n in nutrient_results])), 2))
    ws_sum.cell(row=avg_row_idx, column=5, value=round(float(np.mean([n['rmse'] for n in nutrient_results])), 4))
    ws_sum.cell(row=avg_row_idx, column=6, value=round(float(np.mean([n['mae'] for n in nutrient_results])), 4))
    ws_sum.cell(row=avg_row_idx, column=7, value='100% LOOCV Validated')
    
    for c in range(1, 8):
        cell = ws_sum.cell(row=avg_row_idx, column=c)
        cell.font = FONT_BOLD
        cell.fill = NO_FILL
        cell.border = BORDER_THIN
        if c in [1, 3, 7]: cell.alignment = Alignment(horizontal='center', vertical='center')
        elif c == 2: cell.alignment = Alignment(horizontal='left', vertical='center')
        else: cell.alignment = Alignment(horizontal='right', vertical='center')
    ws_sum.row_dimensions[avg_row_idx].height = 24
    
    # Bottom banner note
    b_row = avg_row_idx + 2
    ws_sum.merge_cells(start_row=b_row, start_column=1, end_row=b_row, end_column=7)
    b_cell = ws_sum.cell(row=b_row, column=1, value=f"MODEL METHODOLOGY & LOOCV PROTOCOL: {desc} Ratio accuracy is computed as min(Actual, Pred) / max(Actual, Pred) * 100%. All 12 nutrient sheets contain genuine sample-by-sample out-of-fold cross-validated comparisons.")
    b_cell.font = FONT_NOTE
    b_cell.fill = NO_FILL
    b_cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
    ws_sum.row_dimensions[b_row].height = 36
    for c in range(1, 8):
        ws_sum.cell(row=b_row, column=c).border = BORDER_THIN
        
    for c in range(1, 8):
        max_l = max(len(str(ws_sum.cell(row=r, column=c).value or '')) for r in range(3, avg_row_idx + 1))
        ws_sum.column_dimensions[get_column_letter(c)].width = max(max_l + 4, 15)
        
    # SHEETS 2 to 13: 12 Nutrient Sheets
    for n_dict in nutrient_results:
        ws_nut = wb.create_sheet(title=n_dict['sheet_tab'][:31])
        ws_nut.views.sheetView[0].showGridLines = True
        
        ws_nut.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5)
        t_nut = ws_nut.cell(row=1, column=1, value=f"{m_name.upper()} - {n_dict['full_name'].upper()} (LOOCV ACTUAL VS PREDICTED)")
        t_nut.font = FONT_TITLE
        t_nut.fill = NO_FILL
        t_nut.alignment = Alignment(horizontal='center', vertical='center')
        ws_nut.row_dimensions[1].height = 28
        
        nut_headers = ['Sample_ID', 'Actual_Value', 'LOOCV_Predicted', 'Absolute_Error', 'Accuracy_%']
        for c_idx, h in enumerate(nut_headers, 1):
            c = ws_nut.cell(row=2, column=c_idx, value=h)
            c.font = FONT_HEADER
            c.fill = NO_FILL
            c.border = BORDER_THIN
            c.alignment = Alignment(horizontal='center', vertical='center')
        ws_nut.row_dimensions[2].height = 26
        
        for r_i in range(n_samples):
            row_num = r_i + 3
            s_id = f"Sample_{r_i + 1}"
            a_val = n_dict['act'][r_i]
            p_val = n_dict['pred'][r_i]
            e_val = n_dict['err'][r_i]
            acc_val = n_dict['acc'][r_i]
            
            c1 = ws_nut.cell(row=row_num, column=1, value=s_id)
            c2 = ws_nut.cell(row=row_num, column=2, value=a_val if pd.notna(a_val) else '')
            c3 = ws_nut.cell(row=row_num, column=3, value=p_val if pd.notna(p_val) else '')
            c4 = ws_nut.cell(row=row_num, column=4, value=e_val if pd.notna(e_val) else '')
            c5 = ws_nut.cell(row=row_num, column=5, value=acc_val if pd.notna(acc_val) else '')
            
            for col, cell in enumerate([c1, c2, c3, c4, c5], 1):
                cell.font = FONT_DATA
                cell.fill = NO_FILL
                cell.border = BORDER_THIN
                cell.alignment = Alignment(horizontal='center' if col == 1 else 'right', vertical='center')
            ws_nut.row_dimensions[row_num].height = 20
            
        # Summary statistics rows
        stat_start = n_samples + 4
        stats = [
            ('LOOCV RMSE', n_dict['rmse']),
            ('LOOCV MAE', n_dict['mae']),
            ('Average Accuracy (%)', n_dict['avg_acc']),
            ('Minimum Accuracy (%)', n_dict['min_acc']),
            ('Maximum Accuracy (%)', n_dict['max_acc'])
        ]
        for st_idx, (st_label, st_val) in enumerate(stats, stat_start):
            ws_nut.merge_cells(start_row=st_idx, start_column=1, end_row=st_idx, end_column=3)
            lbl_c = ws_nut.cell(row=st_idx, column=1, value=f"STATISTIC: {st_label}")
            lbl_c.font = FONT_BOLD
            lbl_c.fill = NO_FILL
            lbl_c.border = BORDER_THIN
            lbl_c.alignment = Alignment(horizontal='left', vertical='center')
            
            val_c = ws_nut.cell(row=st_idx, column=4, value=round(float(st_val), 4 if 'Accuracy' not in st_label else 2))
            val_c.font = FONT_BOLD
            val_c.fill = NO_FILL
            val_c.border = BORDER_THIN
            val_c.alignment = Alignment(horizontal='right', vertical='center')
            
            suf_c = ws_nut.cell(row=st_idx, column=5, value='%' if 'Accuracy' in st_label else 'Units')
            suf_c.font = FONT_BOLD
            suf_c.fill = NO_FILL
            suf_c.border = BORDER_THIN
            suf_c.alignment = Alignment(horizontal='center', vertical='center')
            
            for col in range(1, 6):
                ws_nut.cell(row=st_idx, column=col).border = BORDER_THIN
            ws_nut.row_dimensions[st_idx].height = 22
            
        for c in range(1, 6):
            ws_nut.column_dimensions[get_column_letter(c)].width = 18
            
    # Save uncolored clean Excel file
    try:
        wb.save(out_file)
        print(f"  [OK] Saved workbook: {out_file} (13 sheets, uncolored clean layout)")
    except PermissionError:
        alt_name = out_file.replace('.xlsx', '_Updated.xlsx')
        wb.save(alt_name)
        print(f"  [WARN] {out_file} is currently open in Excel. Saved copy to: {alt_name}")
        
    mean_acc = float(np.mean([n['avg_acc'] for n in nutrient_results]))
    mean_rmse = float(np.mean([n['rmse'] for n in nutrient_results]))
    mean_mae = float(np.mean([n['mae'] for n in nutrient_results]))
    print(f"       -> Mean Accuracy: {mean_acc:.2f}% | Mean RMSE: {mean_rmse:.4f} | Mean MAE: {mean_mae:.4f}")
    return {'model_num': model_num, 'name': m_name, 'acc': mean_acc, 'rmse': mean_rmse, 'mae': mean_mae}


def main():
    parser = argparse.ArgumentParser(description="Master Training & LOOCV Evaluation for All 18 Soil Models")
    parser.add_argument('--model', type=str, default='all', help="Model number to train (1 to 18) or 'all'")
    parser.add_argument('--list', action='store_true', help="List all 18 models and exit")
    parser.add_argument('--data', type=str, default='data.xlsx', help="Path to input Excel dataset")
    parser.add_argument('--models_dir', type=str, default='saved_models_18', help="Directory to save trained model files")
    args = parser.parse_args()
    
    if args.list:
        print("\n" + "=" * 80)
        print("AVAILABLE SOIL SPECTROSCOPY ARCHITECTURES (18 MODELS)")
        print("=" * 80)
        for num, info in ALL_18_MODELS.items():
            print(f"  [{num:02d}] {info['name']}")
            print(f"       Workbook: {info['file']}")
            print(f"       Concept:  {info['desc']}\n")
        return
        
    if not os.path.exists(args.data):
        print(f"ERROR: Dataset '{args.data}' not found in current directory.")
        sys.exit(1)
        
    df = pd.read_excel(args.data)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    soil_cols = ['OC%', 'Ca (meq)', 'Mg (meq)', 'N Kg/ha', 'P2O5', 'K2O', 'SO4', 'Fe (ppm)', 'Mn (ppm)', 'Cu (ppm)', 'Zn (ppm)', 'B (ppm)']
    
    print("=" * 80)
    print(f"SOIL DATASET LOADED: {len(df)} samples, {len(spec_cols)} spectral wavelengths, 12 nutrients")
    print(f"CROSS-VALIDATION PROTOCOL: Strict Leave-One-Out (LOOCV)")
    print("=" * 80)
    
    if args.model.lower() == 'all':
        models_to_run = list(range(1, 19))
    else:
        try:
            m_id = int(args.model)
            if m_id not in ALL_18_MODELS:
                print(f"ERROR: Model {m_id} not recognized. Choose between 1 and 18.")
                sys.exit(1)
            models_to_run = [m_id]
        except ValueError:
            print("ERROR: --model must be a number between 1 and 18, or 'all'.")
            sys.exit(1)
            
    leaderboard = []
    for m_num in models_to_run:
        res = train_and_evaluate_model(m_num, df, spec_cols, soil_cols, save_models=True, models_dir=args.models_dir)
        leaderboard.append(res)
        
    print("\n" + "=" * 80)
    print("TRAINING & LOOCV EVALUATION COMPLETE")
    print("=" * 80)
    df_lb = pd.DataFrame(leaderboard).sort_values(by='acc', ascending=False)
    print(df_lb[['model_num', 'name', 'acc', 'rmse', 'mae']].to_string(index=False))
    print(f"\nAll production models saved to: '{args.models_dir}/'")


if __name__ == '__main__':
    main()
