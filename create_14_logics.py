import os

os.makedirs('logics/implementations', exist_ok=True)

base_template = """
import numpy as np

def predict(s, d):
    try:
        if not d or 'vals' not in d or 'mid' not in d:
            return 0.0
            
        vals = d['vals']
        mid = d['mid']
        indices = d.get('indices', list(range(len(mid[0]) if mid else 21)))
        
        s_arr = np.array(s)
        
        preds = []
        for i, val in enumerate(vals):
            cal_vec = np.array(mid[i])
            if len(cal_vec) != len(s_arr):
                continue
                
            # {custom_logic}
            
            dist = max(dist, 1e-6)
            preds.append((val, 1.0 / dist))
            
        if not preds: return 0.0
        
        num = sum(v * w for v, w in preds)
        den = sum(w for _, w in preds)
        return num / den if den > 0 else 0.0
        
    except Exception:
        return 0.0
"""

logics = {
    'L1': "dist = np.mean(np.abs(s_arr[indices] - cal_vec[indices]) / (np.abs(cal_vec[indices]) + 1e-6))",
    'L2': "dist = np.mean(np.abs(np.log1p(s_arr[indices]) - np.log1p(cal_vec[indices])))",
    'L3': "dist = np.linalg.norm((s_arr[indices] / (np.max(s_arr)+1e-6)) - (cal_vec[indices] / (np.max(cal_vec)+1e-6)))",
    'L4': "weights = np.linspace(1, 2, len(indices)); dist = np.sum(weights * np.abs(s_arr[indices] - cal_vec[indices]))",
    'L5': "dist = np.max(np.abs(s_arr[indices] - cal_vec[indices]))",
    'L6': "dist = np.sum((s_arr[indices] - cal_vec[indices])**2)",
    'L7': "dist = np.sum(np.abs(np.argsort(s_arr[indices]) - np.argsort(cal_vec[indices])))",
    'SPEC1': "from scipy.fftpack import dct; dist = np.linalg.norm(dct(s_arr) - dct(cal_vec))",
    'SPEC2': "from scipy.fftpack import dct; dist = np.linalg.norm(dct(s_arr)[:12] - dct(cal_vec)[:12])",
    'SPEC3': "dist = np.linalg.norm(np.diff(s_arr) - np.diff(cal_vec))", 
    'SPEC4': "dist = np.linalg.norm(np.diff(s_arr, n=2) - np.diff(cal_vec, n=2))", 
    'SPEC5': "dist = np.linalg.norm(np.abs(np.fft.fft(s_arr))[:15] - np.abs(np.fft.fft(cal_vec))[:15])",
    'FP': "dist = np.linalg.norm(np.tanh(s_arr) - np.tanh(cal_vec))",
    'SGSV': "dist = np.linalg.norm(np.gradient(np.gradient(s_arr)) - np.gradient(np.gradient(cal_vec)))"
}

for name, logic in logics.items():
    code = base_template.replace('# {custom_logic}', logic)
    with open(f'logics/implementations/{name}.py', 'w') as f:
        f.write(code.strip())
        
print("Successfully created 14 advanced logic files.")
