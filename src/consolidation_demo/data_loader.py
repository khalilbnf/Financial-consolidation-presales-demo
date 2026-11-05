"""Read the four explicit CSV inputs without inferring identifier types."""
from pathlib import Path
import pandas as pd


def load_data(folder: Path) -> dict[str, pd.DataFrame]:
    """Load source tables; missing files raise an actionable filesystem error."""
    return {name: pd.read_csv(folder / f"{name}.csv", dtype={
        "entity_id": str, "account_code": str, "counterparty_id": str,
    }) for name in ("entities", "trial_balances", "intercompany", "fx_rates")}
