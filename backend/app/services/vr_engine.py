def calculate_stress_index(heart_rate: float, hrv_rmssd: float | None = None) -> float:
    """Derive a 0-100 stress index from HR elevation and HRV suppression.

    Baseline: resting HR ~60-80 bpm maps to low stress; HRV (RMSSD) above
    ~50ms maps to low stress. When HRV is unavailable, HR alone drives the
    index so telemetry still works for basic wearables.
    """
    hr_component = 0.0
    if heart_rate is not None:
        hr = min(max(heart_rate, 30.0), 200.0)
        hr_component = max(0.0, min(100.0, (hr - 60.0) * 1.4))

    if hrv_rmssd is None:
        return round(hr_component, 1)

    hrv = min(max(hrv_rmssd, 5.0), 120.0)
    hrv_component = max(0.0, min(100.0, (60.0 - hrv) * 1.2))

    index = hr_component * 0.55 + hrv_component * 0.45
    return round(index, 1)
