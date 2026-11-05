"""Reconcile reciprocal records before creating elimination journals."""
import pandas as pd
from .fx_translation import translate

TOLERANCE = 0.005


def match_intercompany(records: pd.DataFrame, rates: pd.DataFrame) -> pd.DataFrame:
    """Return both sides, rates, and the EUR difference for each matched pair."""
    source = records.copy()
    source["rate_type"] = source["kind"].map({"service": "average", "balance": "closing"})
    translated = translate(source, rates)
    rows = []
    for transaction_id, pair in translated.groupby("transaction_id", sort=True):
        if len(pair) != 2:
            raise ValueError(f"Intercompany {transaction_id}: expected two reciprocal records")
        a, b = pair.iloc[0], pair.iloc[1]
        difference = round(float(pair.amount_eur.sum()), 2)
        if (a.entity_id != b.counterparty_id or b.entity_id != a.counterparty_id
                or a.entity_id == b.entity_id or a.kind != b.kind
                or a.amount_eur * b.amount_eur >= 0 or abs(difference) > TOLERANCE):
            raise ValueError(f"Intercompany mismatch: {transaction_id} (EUR {difference:,.2f})")
        rows.append({"transaction_id": transaction_id, "kind": a.kind,
                     "entity_a": a.entity_id, "entity_b": b.entity_id,
                     "local_amount_a": a.amount, "currency_a": a.currency, "rate_a": a.rate,
                     "local_amount_b": b.amount, "currency_b": b.currency, "rate_b": b.rate,
                     "amount_eur": abs(a.amount_eur), "difference_eur": difference,
                     "status": "Matched"})
    return pd.DataFrame(rows)


def elimination_journals(records: pd.DataFrame, rates: pd.DataFrame,
                         balances: pd.DataFrame) -> pd.DataFrame:
    """Reverse matched source postings; debit positive and credit negative."""
    match_intercompany(records, rates)
    source = records.copy()
    source["rate_type"] = source.kind.map({"service": "average", "balance": "closing"})
    source = translate(source, rates)
    rows = []
    for row in source.itertuples():
        account = balances[(balances.entity_id == row.entity_id)
                           & (balances.account_code == row.account_code)].iloc[0]
        rows.append({"journal_id": f"IC-{row.transaction_id}", "entity_id": row.entity_id,
                     "account_code": row.account_code, "account_name": account.account_name,
                     "category": account.category, "amount_eur": -row.amount_eur,
                     "explanation": f"Eliminate internal {row.kind}: {row.transaction_id}"})
    return pd.DataFrame(rows)
