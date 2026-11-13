from logics.implementations.logic_utils import logic31_predict, wrap_details

def predict(s, d, target="All"):
    if not d:
        return {
            "value": 0.0,
            "details": {"error": f"INCOMPLETE: Calibration data is required for {target}."}
        }
    val = logic31_predict(s, d, target)
    return wrap_details(val, "Mid_Anchor_Pred", target)
