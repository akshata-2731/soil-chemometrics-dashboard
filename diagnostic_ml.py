import joblib
import pandas as pd
import numpy as np

WAVELENGTH_ORDER = [410,435,460,485,510,535,560,585,610,645,680,705,730,760,810,860,900,940,320,280,200]
FEATURE_NAMES = ["nm_" + str(nm) for nm in WAVELENGTH_ORDER]

# Load sample 1
df = pd.read_excel('data/data.xlsx')
df.fillna(0, inplace=True)
s = df.iloc[0].to_dict()

wvs = []
for nm in WAVELENGTH_ORDER:
    val = s.get("nm_" + str(nm), s.get(str(nm), s.get(nm, 0)))
    try:
        v = float(val)
        if v != v: v = 0.0
    except:
        v = 0.0
    wvs.append(v)

print(f"Testing with Sample: {s.get('Sample_ID', 'Sample 1')}")

for target in ['OC']: # Test OC, N, P...
    model_path = f"models/{target}_model.pkl"
    print(f"\n--- Loading {model_path} ---")
    
    try:
        model_payload = joblib.load(model_path)
    except Exception as e:
        print(f"Error loading {model_path}: {e}")
        continue
        
    print(f"1. Model type: {type(model_payload)}")
    
    if isinstance(model_payload, dict) and "model" in model_payload:
        print("Model is a dict containing 'model'. Unpacking...")
        m_obj = model_payload["model"]
        scaler = m_obj["scaler"]
        classifier = m_obj["classifier"]
        regressors = m_obj["regressors"]
        features = model_payload.get("features", FEATURE_NAMES)
        features_used = list(features)
        
        input_df = pd.DataFrame([wvs], columns=FEATURE_NAMES)[features_used]
        
        print("Preprocessing input with scaler.transform()...")
        X_scaled = scaler.transform(input_df.values)
        print(f"X_scaled values (first 5): {X_scaled[0][:5]}")
        
        pred_class = classifier.predict(X_scaled)[0]
        print(f"2. Classifier selected class: {pred_class}")
        
        reg = regressors.get(pred_class)
        print(f"3. Regressor for class {pred_class}: {type(reg)}")
        
        pred = float(reg.predict(X_scaled)[0])
        print(f"-> EXPLICIT REGRESSOR PREDICTION: {pred}")
        
        if hasattr(model_payload, "predict") or hasattr(m_obj, "predict"):
            print("Note: The model payload or m_obj also has a predict() method!")
            
    else:
        print("Model is a unified object.")
        input_df = pd.DataFrame([wvs], columns=FEATURE_NAMES)
        if hasattr(model_payload, "predict"):
            pred = float(model_payload.predict(input_df.values)[0])
            print(f"-> EXPLICIT UNIFIED PREDICTION: {pred}")
        else:
            print("No predict() method found on model payload.")
