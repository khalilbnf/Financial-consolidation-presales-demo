"""Allocate subsidiary profit and equity under constant direct ownership."""
import pandas as pd


def calculate_minority(entities: pd.DataFrame, translated: pd.DataFrame) -> pd.DataFrame:
    """Calculate allocations without proportionately consolidating subsidiaries."""
    rows = []
    for entity in entities[~entities.is_parent].itertuples():
        balances = translated[translated.entity_id == entity.entity_id]
        profit = -balances.loc[balances.category.isin(["revenue", "expense"]), "amount_eur"].sum()
        opening = -balances.loc[balances.category == "equity", "amount_eur"].sum()
        minority = 1 - entity.ownership
        rows.append({"entity_id": entity.entity_id, "ownership": entity.ownership,
                     "minority_percentage": round(minority, 6), "net_income": round(profit, 2),
                     "parent_profit": round(profit * entity.ownership, 2),
                     "minority_profit": round(profit * minority, 2),
                     "opening_equity": round(opening, 2),
                     "opening_minority": round(opening * minority, 2),
                     "closing_minority": round((opening + profit) * minority, 2)})
    return pd.DataFrame(rows)
