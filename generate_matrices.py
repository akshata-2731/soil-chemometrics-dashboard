import pandas as pd
import numpy as np
import json
import os
import warnings
warnings.filterwarnings('ignore')

# 1. LOAD DATA
df = pd.read_excel('data/data.xlsx')

NUTRIENT_MAP = {
    'OC%': 'OC', 'N Kg/ha': 'N', 'P2O5': 'P', 'K2O': 'K', 'SO4': 'S', 
    'Fe (ppm)': 'Fe', 'Mn (ppm)': 'Mn', 'Cu (ppm)': 'Cu', 'Zn (ppm)': 'Zn', 
    'B (ppm)': 'B', 'Ca (meq)': 'Ca', 'Mg (meq)': 'Mg'
}

# 2. CALCULATE IPS FOR ALL SAMPLES
def calc_ip1(row):
    group = [row['nm_410'], row['nm_435'], row['nm_460'], row['nm_485'], 
             row['nm_510'], row['nm_535'], row['nm_560'], row['nm_585'], row['nm_940']]
    return (sum(x**2 for x in group) / sum(group)) / 100.0

def calc_ip2(row):
    group = [row['nm_610'], row['nm_680'], row['nm_645'], row['nm_730'], 
             row['nm_320'], row['nm_280'], row['nm_200'], row['nm_900'], row['nm_705']]
    return (sum(x**2 for x in group) / sum(group)) / 100.0

def calc_ip3(row):
    group = [row['nm_320'], row['nm_280'], row['nm_200']]
    return (sum(x**2 for x in group) / sum(group)) / 100.0

df['ip1'] = df.apply(calc_ip1, axis=1)
df['ip2'] = df.apply(calc_ip2, axis=1)
df['ip3'] = df.apply(calc_ip3, axis=1)
df['sri'] = (df['ip1'] * df['ip3']) / (df['ip2'] + 1e-10)

matrices = {}

# 3. GENERATE CENTROIDS AND RULES FOR EACH NUTRIENT
for col, short in NUTRIENT_MAP.items():
    if col not in df.columns: continue
    
    # Drop NaNs and zeros
    sub = df[df[col] > 0].copy()
    if len(sub) < 5: continue
    
    # Split into 3 classes based on quantiles (Low = bottom 33%, Med = middle 33%, High = top 33%)
    q33 = sub[col].quantile(0.333)
    q66 = sub[col].quantile(0.666)
    
    # If the data has no variance, fallback
    if q33 == q66:
        q33 = sub[col].min() + 0.01
        q66 = sub[col].max() - 0.01
        
    def assign_class(v):
        if v < q33: return 'Low'
        elif v < q66: return 'Medium'
        else: return 'High'
        
    sub['Class'] = sub[col].apply(assign_class)
    
    # Calculate matrices
    centroids = {}
    sri_ranges = {}
    covariances = {}
    
    for cls in ['Low', 'Medium', 'High']:
        cls_df = sub[sub['Class'] == cls]
        
        # Fallback if empty class
        if len(cls_df) == 0:
            cls_df = sub
            
        c_ip1 = float(cls_df['ip1'].mean())
        c_ip2 = float(cls_df['ip2'].mean())
        c_ip3 = float(cls_df['ip3'].mean())
        centroids[cls] = [c_ip1, c_ip2, c_ip3]
        
        sri_ranges[cls] = {
            'sri_min': float(cls_df['sri'].min()),
            'sri_max': float(cls_df['sri'].max()),
            'val_min': float(cls_df[col].min()),
            'val_max': float(cls_df[col].max())
        }
        
        # Calculate covariance matrix for Mahalanobis
        matrix = np.cov(cls_df[['ip1', 'ip2', 'ip3']].T) + np.eye(3)*0.001
        try:
            inv_cov = np.linalg.inv(matrix).tolist()
        except:
            inv_cov = np.eye(3).tolist()
        covariances[cls] = inv_cov

    # Simple HIGH Rules
    high_df = sub[sub['Class'] == 'High']
    if len(high_df) > 0:
        high_sri = float(high_df['sri'].quantile(0.1)) # 10th percentile
    else:
        high_sri = 8.0
        
    high_rules = {
        'Group_A': {'sri_threshold': float(high_sri * 1.5)},
        'Group_B': {'sri_threshold': 1.2, 'ip1_threshold': 8.0, 'ip3_threshold': 0.7}
    }
    
    matrices[short] = {
        'centroids': centroids,
        'covariances': covariances,
        'sri_ranges': sri_ranges,
        'high_rules': high_rules
    }

# Ensure Nitrogen EXACTLY matches user's request from chat
if 'N' in matrices:
    matrices['N']['centroids'] = {
        'Low': [8.569986, 3.731463, 1.716387],
        'Medium': [10.308449, 3.918395, 3.820572],
        'High': [8.805760, 3.760319, 2.218485]
    }
    matrices['N']['sri_ranges'] = {
        'Low': {'sri_min': 0.2, 'sri_max': 4.0, 'val_min': 0, 'val_max': 150},
        'Medium': {'sri_min': 1.5, 'sri_max': 9.0, 'val_min': 150, 'val_max': 300},
        'High': {'sri_min': 0.1, 'sri_max': 20.0, 'val_min': 300, 'val_max': 500}
    }
    matrices['N']['high_rules'] = {
        'Group_A': {'sri_threshold': 8.0},
        'Group_B': {'sri_threshold': 1.2, 'ip1_threshold': 8.0, 'ip3_threshold': 0.7}
    }

# 4. SAVE TO JSON
with open('logics/implementations/advanced_matrices.json', 'w', encoding='utf-8') as f:
    json.dump(matrices, f, indent=4)

print("Generated advanced_matrices.json successfully!")
