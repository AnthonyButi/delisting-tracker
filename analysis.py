import pandas as pd
from storage import load_panel

# Average months a listing spends in "pending" before closing.
# THE key modeling assumption (Little's Law bridge from stock to flow).
PENDING_DWELL_MONTHS = 1.5

# Map FRED series-ID prefixes to friendly names so the analysis
# doesn't care which metro's IDs are in the panel.
PREFIX_MAP = {
    "ACTLISCOU": "active",
    "NEWLISCOU": "new",
    "PENLISCOU": "pending",
    "PRIREDCOU": "price_reduced",
    "MORTGAGE30US": "mortgage",
}


def tidy_columns(panel):
    """Rename series-ID columns to friendly metric names by prefix."""
    rename = {}
    for col in panel.columns:
        for prefix, name in PREFIX_MAP.items():
            if col.startswith(prefix):
                rename[col] = name
                break
    return panel.rename(columns=rename)


def compute_withdrawals(panel, dwell_months=PENDING_DWELL_MONTHS):
    """
    Derive implied withdrawals from the inventory flow identity.

        exits(t)        = active(t-1) + new(t) - active(t)   # total departures (certain)
        went_pending(t) ~= pending(t) / dwell_months         # stock -> flow (Little's Law)
        withdrawn(t)    = exits(t) - went_pending(t)          # the residual we want
        delisting_rate  = withdrawn(t) / homes available that month

    ASSUMPTION & LIMITATIONS:
    - went_pending is estimated from the pending STOCK via Little's Law,
      assuming an average pending duration of `dwell_months` (default 1.5).
    - The LEVEL of the result is highly sensitive to this value (the rate
      swings from negative to ~18% as dwell goes 1.0 -> 2.5), so absolute
      numbers should not be quoted as fact.
    - The SEASONAL SHAPE is robust to the assumption (winter-high, spring-low,
      January peak hold across all plausible dwell values), so the signal is
      reliable as a DIRECTIONAL indicator, not a calibrated count.
    - dwell = 1.0 produces near-universally negative withdrawals (impossible),
      which empirically rules out durations that short.
    - Method is weakest at turning points, where stock and flow are out of
      sync and Little's Law's steady-state assumption breaks down (see Nov).
    """
    df = tidy_columns(panel).copy()

    df["exits"] = df["active"].shift(1) + df["new"] - df["active"]
    df["went_pending"] = df["pending"] / dwell_months
    df["withdrawn"] = df["exits"] - df["went_pending"]

    df["available"] = df["active"].shift(1) + df["new"]
    df["delisting_rate"] = df["withdrawn"] / df["available"]

    return df

def add_smoothing(result):
    """Add trend views that see past the seasonal swing."""
    df = result.copy()
    # 12-month rolling mean spans a full year -> seasonality averages out,
    # leaving the underlying trend in withdrawal pressure.
    df["rate_trend_%"] = df["delisting_rate"].rolling(12).mean() * 100
    # Year-over-year: each month vs the SAME month last year, so the
    # seasonal component cancels (Jan vs Jan). Result is in percentage points.
    df["rate_yoy_pp"] = (df["delisting_rate"] - df["delisting_rate"].shift(12)) * 100
    return df

def driver_correlations(result):
    """Correlate the delisting rate against its drivers using YoY changes,
    so a shared seasonal rhythm can't manufacture a fake correlation."""
    signals = pd.DataFrame({
        "delisting_rate": result["delisting_rate"].diff(12),
        "mortgage_rate":  result["mortgage"].diff(12),
        "price_reduced":  result["price_reduced"].diff(12),
    })
    return signals.corr()

if __name__ == "__main__":
    panel = load_panel()
    result = compute_withdrawals(panel)
    result["delisting_rate_%"] = result["delisting_rate"] * 100
    result = add_smoothing(result)

    cols = ["active", "withdrawn", "delisting_rate_%", "rate_trend_%", "rate_yoy_pp"]
    print("Withdrawal signal with trend + year-over-year:")
    print(result[cols].tail(14).round(1))

    print("\nYoY correlations (delisting rate vs drivers):")
    print(driver_correlations(result).round(2))

    print("\nDelisting-to-new ratio (national was ~0.27 in Oct 2025, Miami ~0.45):")
    print((result["withdrawn"] / result["new"]).tail(12).round(2))
