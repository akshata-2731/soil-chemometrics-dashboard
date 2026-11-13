from logics.implementations.logic_utils import logic14_predict, wrap_details

def predict(s, d, target="All"):
    if not d:
        # Failsafe if calibration json is completely missing for this target
        return {
            "value": 0.0,
            "details": {"error": f"INCOMPLETE: Calibration data is required for {target}."}
        }
    val = logic14_predict(s, d, target)
    return wrap_details(val, "Confidence_Projection", target)
