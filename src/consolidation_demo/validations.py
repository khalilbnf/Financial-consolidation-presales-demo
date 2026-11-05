"""Fail early rather than silently produce incomplete financial statements."""
import numpy as np
import pandas as pd
from .intercompany import match_intercompany

SCHEMAS = {
    "entities": "entity_id name country currency ownership is_parent",
    "trial_balances": "entity_id account_code account_name category rate_type currency amount",
    "intercompany": "transaction_id kind entity_id counterparty_id account_code currency amount",
    "fx_rates": "currency rate_type rate",
}


def validate_data(data: dict[str, pd.DataFrame]) -> None:
    """Validate source schema, references, model scope and accounting integrity."""
    for name, columns in SCHEMAS.items():
        frame = data[name]
        required = columns.split()
        if not set(required).issubset(frame.columns):
            raise ValueError(f"{name}: missing required columns")
        if frame.empty or frame[required].isna().any().any():
            raise ValueError(f"{name}: missing values or empty input")
        if frame[required].map(lambda x: isinstance(x, str) and not x.strip()).any().any():
            raise ValueError(f"{name}: blank required values")
        if frame.duplicated().any():
            raise ValueError(f"{name}: duplicate records")
    entities, tb, ic, rates = (data[k] for k in SCHEMAS)
    for frame, keys in ((entities, ["entity_id"]), (tb, ["entity_id", "account_code"]),
                        (rates, ["currency", "rate_type"]),
                        (ic, ["transaction_id", "entity_id"])):
        if frame.duplicated(keys).any():
            raise ValueError(f"Duplicate key: {keys}")
    for frame, column in ((entities, "ownership"), (tb, "amount"), (ic, "amount"), (rates, "rate")):
        if not pd.api.types.is_numeric_dtype(frame[column]) or not np.isfinite(frame[column]).all():
            raise ValueError(f"Invalid numeric values: {column}")
    if not entities.ownership.between(0, 1).all():
        raise ValueError("Invalid ownership percentages: expected 0 to 1")
    if not entities.is_parent.isin([True, False]).all() or entities.is_parent.sum() != 1:
        raise ValueError("Exactly one parent required")
    parent = entities[entities.is_parent].iloc[0]
    if parent.ownership != 1 or parent.currency != "EUR":
        raise ValueError("Parent must be wholly owned and report in EUR")
    if (entities.loc[~entities.is_parent, "ownership"] <= 0.5).any():
        raise ValueError("V1 supports directly controlled subsidiaries only")
    if not set(rates.currency).issubset({"EUR", "GBP"}) or (rates.rate <= 0).any():
        raise ValueError("Invalid currencies or FX rates")
    if not set(rates.rate_type).issubset({"opening", "average", "closing"}):
        raise ValueError("Invalid FX rate types")
    for entity in entities.itertuples():
        selected = rates[rates.currency == entity.currency]
        if set(selected.rate_type) != {"opening", "average", "closing"}:
            raise ValueError(f"Missing FX rates: {entity.currency}")
        if selected.rate.nunique() != 1 or (entity.currency == "EUR" and selected.rate.iloc[0] != 1):
            raise ValueError("V1 requires equal opening, average and closing rates; EUR rate must be 1")
    for frame in (tb, ic):
        if not set(frame.entity_id).issubset(set(entities.entity_id)):
            raise ValueError("Unknown entities")
        expected = frame.entity_id.map(entities.set_index("entity_id").currency)
        if not frame.currency.eq(expected).all():
            raise ValueError("Invalid currencies for entity")
    if set(tb.entity_id) != set(entities.entity_id):
        raise ValueError("Missing entity trial balance")
    if not set(tb.category).issubset({"asset", "liability", "equity", "revenue", "expense"}):
        raise ValueError("Invalid account category")
    expected_types = tb.category.map({"asset": "closing", "liability": "closing",
                                     "equity": "opening", "revenue": "average", "expense": "average"})
    expected_types = expected_types.where(tb.account_code != "1300", "opening")
    if not tb.rate_type.eq(expected_types).all():
        raise ValueError("Invalid FX rate type for account")
    if (tb.groupby("entity_id").amount.sum().abs() > 0.005).any():
        raise ValueError("Trial balances are not balanced")
    if not set(ic.counterparty_id).issubset(set(entities.entity_id)):
        raise ValueError("Unknown intercompany counterparty")
    if not set(ic.kind).issubset({"service", "balance"}):
        raise ValueError("Invalid intercompany kind")
    linked = ic.merge(tb, on=["entity_id", "account_code"], suffixes=("", "_tb"), how="left")
    allowed = {"service": {"4100", "5100"}, "balance": {"1200", "2100"}}
    for row in linked.itertuples():
        if pd.isna(row.amount_tb) or row.account_code not in allowed[row.kind]:
            raise ValueError("Invalid intercompany account mapping")
    totals = ic.groupby(["entity_id", "account_code"]).amount.sum()
    recorded = tb[tb.account_code.isin(["4100", "5100", "1200", "2100"])].set_index(
        ["entity_id", "account_code"]).amount
    if not totals.index.equals(recorded.sort_index().index) or not (
            totals.sort_index() - recorded.sort_index()).abs().le(0.005).all():
        raise ValueError("Intercompany records do not reconcile to trial balances")
    match_intercompany(ic, rates)
