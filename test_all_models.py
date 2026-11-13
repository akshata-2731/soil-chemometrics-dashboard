import os
import glob
import pandas as pd
from app import execute_prediction, MODELS_DIR

def verify_all_models():
    print("Loading test data...")
    df = pd.read_excel('data/data.xlsx')
    df.fillna(0, inplace=True)
    # Use the first sample as the test payload
    sample_data = df.iloc[0].to_dict()
    
    # Grab all .pkl files recursively
    all_models = glob.glob(os.path.join(MODELS_DIR, "**", "*.pkl"), recursive=True)
    
    success_count = 0
    fail_count = 0
    
    print(f"Found {len(all_models)} models to verify. Beginning verification...")
    
    for m_path in all_models:
        # Get the method_id exactly as the frontend would send it
        method_id = os.path.relpath(m_path, MODELS_DIR).replace("\\", "/")
        
        # Deduce target from filename (e.g., OC_model.pkl -> OC)
        filename = os.path.basename(m_path)
        target_clean = filename.replace("_model.pkl", "")
        
        # We just need to pass something that the ML pipeline will accept as target
        # The actual numeric target doesn't matter for the prediction itself, 
        # except for soft clamp rules or classification status names.
        target = target_clean # E.g. "OC", "N"
        
        try:
            res = execute_prediction(
                sample_data=sample_data,
                target=target,
                method_type="ml",
                method_id=method_id,
                is_cal_required=False
            )
            success_count += 1
        except Exception as e:
            print(f"FAILED on {method_id}: {str(e)}")
            fail_count += 1
            
    print("\n--- VERIFICATION COMPLETE ---")
    print(f"Total Models Verified: {len(all_models)}")
    print(f"SUCCESS: {success_count}")
    print(f"FAILED: {fail_count}")

if __name__ == "__main__":
    verify_all_models()
