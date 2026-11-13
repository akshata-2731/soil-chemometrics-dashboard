import json, os
os.makedirs('logics/definitions', exist_ok=True)
ids = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'SPEC1', 'SPEC2', 'SPEC3', 'SPEC4', 'SPEC5', 'FP', 'SGSV']
names = [
    'Mid-Anchor Relative Dev', 'Mid-Anchor Logarithmic', 'Channel Normalization', 
    'Sensitivity Weighted', 'Matrix Correction', 'Residual Method', 'Position Engine',
    'DCT', 'DCT Modified', 'DWT', 'DWT Modified', 'FFT', 'Fingerprint + Transform', 'SG/SV Logic'
]

for i, logic_id in enumerate(ids):
    data = {
        "id": logic_id,
        "name": names[i],
        "calibration_required": True,
        "features": []
    }
    with open(f'logics/definitions/{logic_id}.json', 'w') as f:
        json.dump(data, f, indent=4)
print("Done!")
