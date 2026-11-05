"""Explicit local-to-EUR translation, preserving its audit trail."""
import pandas as pd


def translate(balances: pd.DataFrame, rates: pd.DataFrame) -> pd.DataFrame:
    """Apply EUR per local currency unit, rounding each translated row to cents."""
    result = balances.merge(rates, on=["currency", "rate_type"], validate="many_to_one")
    if len(result) != len(balances):
        raise ValueError("Missing FX rates: translation would drop source rows")
    result["amount_eur"] = (result["amount"] * result["rate"]).round(2)
    return result
