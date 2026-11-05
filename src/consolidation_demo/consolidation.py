"""Run the transparent journal-based consolidation and its controls."""
from dataclasses import dataclass
import logging
import pandas as pd
from .validations import validate_data
from .fx_translation import translate
from .intercompany import match_intercompany, elimination_journals
from .minority_interest import calculate_minority

logger = logging.getLogger(__name__)


@dataclass
class ConsolidationResult:
    translated: pd.DataFrame
    matching: pd.DataFrame
    journals: pd.DataFrame
    minority: pd.DataFrame
    pnl: pd.DataFrame
    balance_sheet: pd.DataFrame
    metrics: dict[str, float]
    controls: dict[str, str]


def investment_journals(entities: pd.DataFrame, translated: pd.DataFrame,
                        minority: pd.DataFrame) -> pd.DataFrame:
    """Eliminate investments at opening book value; recognize opening NCI."""
    parent_id = entities.loc[entities.is_parent, "entity_id"].iloc[0]
    investment = translated[(translated.entity_id == parent_id) & (translated.account_code == "1300")]
    expected = round(float((minority.opening_equity * minority.ownership).sum()), 2)
    if abs(investment.amount_eur.sum() - expected) > 0.005:
        raise ValueError("Investments must equal owned opening net assets in V1 (no goodwill)")
    rows = []
    def add(entity_id, code, name, category, amount):
        rows.append(dict(journal_id="INV-001", entity_id=entity_id, account_code=code,
                         account_name=name, category=category, amount_eur=round(amount, 2),
                         explanation="Eliminate opening subsidiary equity and investments; recognize opening NCI"))
    for row in minority.itertuples():
        add(row.entity_id, "3000", "Opening equity", "equity", row.opening_equity)
        if row.opening_minority:
            add(row.entity_id, "3100", "Opening non-controlling interests", "equity", -row.opening_minority)
    add(parent_id, "1300", "Investments in subsidiaries", "asset", -expected)
    return pd.DataFrame(rows)


def consolidate(data: dict[str, pd.DataFrame]) -> ConsolidationResult:
    """Validate, translate, eliminate, allocate and reconcile the group."""
    validate_data(data)
    logger.info("Source validation passed")
    entities, tb, ic, rates = (data[k] for k in ("entities", "trial_balances", "intercompany", "fx_rates"))
    translated = translate(tb, rates)
    matching = match_intercompany(ic, rates)
    minority = calculate_minority(entities, translated)
    journals = pd.concat([elimination_journals(ic, rates, tb),
                          investment_journals(entities, translated, minority)], ignore_index=True)
    if (journals.groupby("journal_id").amount_eur.sum().abs() > 0.005).any():
        raise ValueError("Consolidation journals are not balanced")
    ledger = pd.concat([translated, journals], ignore_index=True)
    def total(category):
        return round(float(ledger.loc[ledger.category == category, "amount_eur"].sum()), 2)
    revenue, expenses = -total("revenue"), total("expense")
    income = round(revenue - expenses, 2)
    assets, liabilities = total("asset"), -total("liability")
    equity = round(-total("equity") + income, 2)
    nci = round(float(minority.closing_minority.sum()), 2)
    minority_profit = round(float(minority.minority_profit.sum()), 2)
    if abs(assets - liabilities - equity) > 0.005:
        raise ValueError("Consolidated Balance Sheet is not balanced")
    metrics = dict(revenue=revenue, operating_profit=income, net_income=income,
                   parent_profit=round(income - minority_profit, 2), minority_profit=minority_profit,
                   assets=assets, liabilities=liabilities, equity=equity,
                   parent_equity=round(equity - nci, 2), minority_equity=nci,
                   entities=len(entities), currencies=entities.currency.nunique(),
                   service_transactions=int((matching.kind == "service").sum()),
                   service_value=float(matching.loc[matching.kind == "service", "amount_eur"].sum()),
                   balance_pairs=int((matching.kind == "balance").sum()),
                   balance_value=float(matching.loc[matching.kind == "balance", "amount_eur"].sum()),
                   journals=journals.journal_id.nunique(),
                   adjustment_debits=float(journals.loc[journals.amount_eur > 0, "amount_eur"].sum()))
    pnl = pd.DataFrame([("Revenue", revenue), ("Operating expenses", -expenses),
                        ("Operating profit", income), ("Net income", income),
                        ("Attributable to parent", income - minority_profit),
                        ("Attributable to non-controlling interests", minority_profit)], columns=["Line", "EUR"])
    bs_rows = []
    for category, sign in (("asset", 1), ("liability", -1)):
        grouped = ledger[ledger.category == category].groupby("account_name").amount_eur.sum()
        bs_rows.extend((name, round(float(value * sign), 2)) for name, value in grouped.items())
        bs_rows.append(("Total assets" if category == "asset" else "Total liabilities", assets if category == "asset" else liabilities))
    bs_rows.extend([("Equity attributable to parent", equity - nci), ("Non-controlling interests", nci),
                    ("Total equity", equity), ("Total liabilities and equity", liabilities + equity),
                    ("Balance check", round(assets - liabilities - equity, 2))])
    controls = {name: "PASS" for name in ["Trial balances balanced", "FX rates available",
                "Intercompany records matched", "Consolidation journals balanced", "Consolidated Balance Sheet balanced"]}
    logger.info("Consolidation complete: all five controls passed")
    return ConsolidationResult(translated, matching, journals, minority, pnl,
                               pd.DataFrame(bs_rows, columns=["Line", "EUR"]), metrics, controls)
